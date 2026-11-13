import hashlib
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from apps.billing.decorators import subscription_required
from apps.core.ratelimit import ratelimit

from .forms import CarSuggestionForm, CommentForm, EntryFilterForm, EntryForm, ParameterFormSet, ReportForm
from .models import Attachment, Bookmark, CarModel, Comment, Entry, Report, Vote

log = logging.getLogger(__name__)

PAGE_SIZE = 20


def _visible():
    return Entry.objects.published().select_related("car_model__make", "author")


def _filtered(request, qs):
    form = EntryFilterForm(request.GET)
    sort = "new"
    if form.is_valid():
        d = form.cleaned_data
        if d["q"]:
            q = d["q"].strip()
            qs = qs.filter(
                Q(title__icontains=q) | Q(engine__icontains=q) | Q(ecu_type__icontains=q)
                | Q(gearbox__icontains=q) | Q(turbo__icontains=q) | Q(car_model__name__icontains=q)
                | Q(car_model__make__name__icontains=q)
            )
        if d["make"]:
            qs = qs.filter(car_model__make=d["make"])
        if d["car_model"]:
            qs = qs.filter(car_model=d["car_model"])
        for field in ("category", "fuel", "stage", "language"):
            if d[field]:
                qs = qs.filter(**{field: d[field]})
        sort = d["sort"] or "new"
    qs = qs.with_stats()
    order = {"top": ["-vote_count", "-created_at"], "discussed": ["-comment_count", "-created_at"]}.get(sort, ["-created_at"])
    return form, qs.order_by(*order)


def home(request):
    """Public teaser list: title / car / category / stats. Details are behind the paywall."""
    form, qs = _filtered(request, _visible())
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "catalog/list.html", {"page": page, "form": form, "total": page.paginator.count})


def detail(request, pk, slug=None):
    entry = get_object_or_404(Entry.objects.select_related("car_model__make", "author"), pk=pk)
    user = request.user
    if entry.status != Entry.Status.PUBLISHED and not entry.can_edit(user):
        raise Http404
    if slug != entry.slug:
        return redirect(entry, permanent=True)

    has_access = user.is_authenticated and user.has_access
    ctx = {"entry": entry, "has_access": has_access}
    ctx["vote_count"] = entry.votes.count()
    if has_access:
        ctx.update(
            comments=entry.comments.select_related("author"),
            parameters=entry.parameters.all(),
            attachments=entry.attachments.all(),
            comment_form=CommentForm(),
            report_form=ReportForm(),
            voted=entry.votes.filter(user=user).exists(),
            bookmarked=entry.bookmarks.filter(user=user).exists(),
            can_edit=entry.can_edit(user),
        )
    else:
        # Teaser for visitors and non-subscribers (SEO + conversion). No body, values or files.
        ctx.update(
            parameter_count=entry.parameters.count(),
            attachment_count=entry.attachments.count(),
            comment_count=entry.comments.count(),
        )
    related = (
        _visible().filter(car_model=entry.car_model).exclude(pk=entry.pk).order_by("-created_at")[:4]
    )
    ctx["related"] = related
    ctx["ld"] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entry.title[:110],
        "about": str(entry.car_model),
        "inLanguage": entry.language,
        "datePublished": entry.created_at.isoformat(),
        "dateModified": entry.updated_at.isoformat(),
        "author": {"@type": "Person", "name": entry.author.display_name if entry.author else "anonymous"},
        "isAccessibleForFree": False,
        "hasPart": {"@type": "WebPageElement", "isAccessibleForFree": False, "cssSelector": ".paywall"},
    }
    return render(request, "catalog/detail.html", ctx)


def _save_entry(request, form, formset):
    with transaction.atomic():
        entry = form.save(commit=False)  # author is set by create() only – edits never change it
        entry.save()
        formset.instance = entry
        params = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for i, p in enumerate(params):
            p.position = p.position or i
            p.save()
        for f in form.cleaned_data.get("attachments") or []:
            digest = hashlib.sha256()
            for chunk in f.chunks():
                digest.update(chunk)
            f.seek(0)
            Attachment.objects.create(
                entry=entry, file=f, original_name=f.name[:200], size=f.size, sha256=digest.hexdigest()
            )
    return entry


@subscription_required
@ratelimit("entry-create", limit=20, period=3600, by="user")
def create(request):
    ui_lang = (translation.get_language() or "pl")[:2]
    initial = {"language": ui_lang if ui_lang in Entry.Language.values else Entry.Language.PL}
    form = EntryForm(request.POST or None, request.FILES or None, initial=initial)
    formset = ParameterFormSet(request.POST or None, prefix="params")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        form.instance.author = request.user
        entry = _save_entry(request, form, formset)
        messages.success(request, _("Entry published."))
        return redirect(entry)
    return render(request, "catalog/form.html", {"form": form, "formset": formset})


@subscription_required
def edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    if not entry.can_edit(request.user):
        return HttpResponseForbidden()
    form = EntryForm(request.POST or None, request.FILES or None, instance=entry)
    formset = ParameterFormSet(request.POST or None, instance=entry, prefix="params")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        entry = _save_entry(request, form, formset)
        messages.success(request, _("Changes saved."))
        return redirect(entry)
    return render(
        request, "catalog/form.html",
        {"form": form, "formset": formset, "entry": entry, "attachments": entry.attachments.all()},
    )


@subscription_required
def delete(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    if not entry.can_edit(request.user):
        return HttpResponseForbidden()
    if request.method == "POST":
        entry.delete()  # attachments cascade; their files are removed by a post_delete signal
        messages.success(request, _("Entry deleted."))
        return redirect("catalog:mine")
    return render(request, "catalog/confirm_delete.html", {"entry": entry})


@subscription_required
@require_POST
def delete_attachment(request, pk):
    att = get_object_or_404(Attachment.objects.select_related("entry"), pk=pk)
    if not att.entry.can_edit(request.user):
        return HttpResponseForbidden()
    entry = att.entry
    att.delete()
    messages.success(request, _("Attachment removed."))
    return redirect("catalog:edit", pk=entry.pk)


@subscription_required
@require_POST
@ratelimit("vote", limit=60, period=600, by="user")
def toggle_vote(request, pk):
    entry = get_object_or_404(_visible(), pk=pk)
    if entry.author_id == request.user.pk:
        messages.info(request, _("You cannot vote for your own entry."))
        return redirect(entry)
    deleted, _n = Vote.objects.filter(entry=entry, user=request.user).delete()
    if not deleted:
        try:
            with transaction.atomic():
                Vote.objects.create(entry=entry, user=request.user)
        except IntegrityError:  # double click / concurrent request
            pass
    return redirect(entry)


@subscription_required
@require_POST
def toggle_bookmark(request, pk):
    entry = get_object_or_404(_visible(), pk=pk)
    deleted, _n = Bookmark.objects.filter(entry=entry, user=request.user).delete()
    if not deleted:
        try:
            with transaction.atomic():
                Bookmark.objects.create(entry=entry, user=request.user)
        except IntegrityError:  # double click / concurrent request
            pass
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(entry)


def _notify_author(request, entry, comment):
    author = entry.author
    if not author or author.pk == comment.author_id or not author.notify_comments or not author.is_active:
        return
    link = request.build_absolute_uri(entry.get_absolute_url())
    with translation.override(author.preferred_language):
        send_mail(
            _("New comment on “%(title)s”") % {"title": entry.title},
            _("%(user)s commented on your entry:\n\n%(body)s\n\n%(link)s\n\nYou can turn these emails off in your account settings.")
            % {"user": comment.author.display_name, "body": comment.body[:500], "link": link},
            settings.DEFAULT_FROM_EMAIL,
            [author.email],
            fail_silently=True,
        )


@subscription_required
@require_POST
@ratelimit("comment", limit=10, period=300, by="user")
def add_comment(request, pk):
    entry = get_object_or_404(_visible(), pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.entry, c.author = entry, request.user
        c.save()
        _notify_author(request, entry, c)
    return redirect(entry.get_absolute_url() + "#comments")


@subscription_required
@require_POST
def delete_comment(request, pk):
    c = get_object_or_404(Comment.objects.select_related("entry"), pk=pk)
    if not (request.user.is_staff or c.author_id == request.user.pk):
        return HttpResponseForbidden()
    entry = c.entry
    c.delete()
    return redirect(entry.get_absolute_url() + "#comments")


@subscription_required
@require_POST
@ratelimit("report", limit=10, period=3600, by="user")
def report(request, pk):
    entry = get_object_or_404(_visible(), pk=pk)
    form = ReportForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                r = form.save(commit=False)
                r.entry, r.reporter = entry, request.user
                r.save()
        except IntegrityError:
            messages.info(request, _("You have already reported this entry."))
            return redirect(entry)
        open_reports = entry.reports.filter(resolved=False).values("reporter").distinct().count()
        if open_reports >= Report.AUTO_HIDE_THRESHOLD:
            Entry.objects.filter(pk=entry.pk).update(status=Entry.Status.HIDDEN)
            log.warning("Entry %s auto-hidden after %s reports", entry.pk, open_reports)
        messages.success(request, _("Thank you. A moderator will review your report."))
    return redirect(entry)


@subscription_required
def download_attachment(request, pk):
    att = get_object_or_404(Attachment.objects.select_related("entry"), pk=pk)
    if att.entry.status != Entry.Status.PUBLISHED and not att.entry.can_edit(request.user):
        raise Http404
    try:
        fh = att.file.open("rb")
    except FileNotFoundError:
        raise Http404
    Attachment.objects.filter(pk=att.pk).update(download_count=F("download_count") + 1)
    resp = FileResponse(fh, as_attachment=True, filename=att.original_name, content_type="application/octet-stream")
    resp["X-Content-Type-Options"] = "nosniff"
    resp["Cache-Control"] = "private, no-store"
    return resp


@subscription_required
def saved(request):
    mine = Bookmark.objects.filter(user=request.user)
    qs = (
        Entry.objects.published()
        .filter(pk__in=mine.values("entry"))
        .annotate(saved_at=Subquery(mine.filter(entry=OuterRef("pk")).values("created_at")[:1]))
        .select_related("car_model__make", "author")
        .with_stats()
        .order_by("-saved_at")
    )
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "catalog/collection.html", {"page": page, "heading": _("Saved entries")})


@subscription_required
def mine(request):
    qs = Entry.objects.filter(author=request.user).select_related("car_model__make", "author").with_stats().order_by("-created_at")
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "catalog/collection.html", {"page": page, "heading": _("My entries"), "show_status": True})


@subscription_required
@ratelimit("car-suggest", limit=10, period=86400, by="user")
def suggest_car(request):
    form = CarSuggestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        s = form.save(commit=False)
        s.user = request.user
        s.save()
        messages.success(request, _("Thank you! A moderator will add the car to the catalogue soon."))
        return redirect("catalog:create")
    return render(
        request, "_form_page.html",
        {"form": form, "page_title": _("Suggest a missing car"), "submit_label": _("Send suggestion")},
    )


@cache_page(60 * 5)
def models_for_make(request):
    """Public catalogue data for the dependent make → model dropdown."""
    make = request.GET.get("make", "")
    if not make.isdigit():
        return JsonResponse({"models": []})
    models = [
        {"id": m.pk, "label": " ".join(p for p in (m.name, m.generation) if p) + (f" ({m.years})" if m.years else "")}
        for m in CarModel.objects.filter(make_id=make)
    ]
    return JsonResponse({"models": models})


def makes_overview(request):
    """Public browse page: makes with entry counts."""
    from .models import Make

    makes = (
        Make.objects.annotate(n=Count("models__entries", filter=Q(models__entries__status=Entry.Status.PUBLISHED)))
        .order_by("-n", "name")
    )
    return render(request, "catalog/makes.html", {"makes": makes, "list_url": reverse("catalog:home")})
