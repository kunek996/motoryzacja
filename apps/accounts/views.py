import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.core.ratelimit import client_ip, count, incr, ratelimit, reset

from .forms import DeleteAccountForm, ProfileForm, ResendVerificationForm, SignupForm
from .models import User

VERIFY_SALT = "accounts.verify-email"
VERIFY_MAX_AGE = 60 * 60 * 48  # 48 h


def _send_verification(request, user):
    token = signing.dumps({"uid": user.pk, "email": user.email}, salt=VERIFY_SALT)
    link = request.build_absolute_uri(reverse("accounts:verify", args=[token]))
    with translation.override(user.preferred_language):
        send_mail(
            _("Confirm your email address"),
            _("Welcome! Confirm your email by opening this link (valid 48 hours):\n%(link)s")
            % {"link": link},
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )


@ratelimit("signup", limit=5, period=3600)
def signup(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        now = timezone.now()
        user.terms_accepted_at = now
        user.privacy_accepted_at = now
        user.marketing_consent = form.cleaned_data["marketing_consent"]
        user.preferred_language = translation.get_language() or "pl"
        user.save()
        _send_verification(request, user)
        return render(request, "accounts/check_email.html")
    return render(request, "accounts/signup.html", {"form": form})


def verify_email(request, token):
    """Marks the address as confirmed. Deliberately does NOT log the visitor in:
    - a link is not proof of knowing the password (someone else may have registered the address,
      the owner then recovers access via password reset, which also confirms the email);
    - logging in from a link would allow login CSRF (victim silently signed into an attacker's account).
    """
    try:
        data = signing.loads(token, salt=VERIFY_SALT, max_age=VERIFY_MAX_AGE)
        user = User.objects.get(pk=data["uid"], email=data.get("email"), is_active=True)
    except (signing.BadSignature, User.DoesNotExist, KeyError, TypeError):
        messages.error(request, _("This confirmation link is invalid or has expired."))
        return redirect("accounts:login")
    if user.email_verified:
        messages.info(request, _("Your email address is already confirmed. Please log in."))
    else:
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        messages.success(request, _("Email confirmed. You can now log in."))
    return redirect("accounts:login")


@ratelimit("resend-verify", limit=3, period=3600)
def resend_verification(request):
    form = ResendVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(email__iexact=form.cleaned_data["email"], email_verified=False, is_active=True).first()
        if user:
            _send_verification(request, user)
        # Same answer whether or not the account exists (no account enumeration).
        return render(request, "accounts/check_email.html")
    return render(
        request, "_form_page.html",
        {"form": form, "page_title": _("Resend confirmation email"), "submit_label": _("Send")},
    )


class LoginView(auth_views.LoginView):
    """Login throttling that only counts FAILED attempts, so nobody can lock out a real user
    just by posting their email:
      - per IP:              20 failures / 10 min (credential stuffing from one source)
      - per account + IP:     8 failures / 15 min (guessing one password)
      - per account (global): 100 failures / hour  (distributed guessing; high enough to make
                              a lock-out attack expensive, Argon2 makes guessing slow anyway)
    """

    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    LIMITS = (("ip", 20, 600), ("acct-ip", 8, 900), ("acct", 100, 3600))

    def _keys(self, request):
        email = (request.POST.get("username") or "").strip().lower()[:254]
        ip = client_ip(request)
        return {"ip": f"login-fail-ip:{ip}", "acct-ip": f"login-fail:{email}:{ip}", "acct": f"login-fail:{email}"}

    def post(self, request, *args, **kwargs):
        enabled = getattr(settings, "RATELIMIT_ENABLED", True)
        keys = self._keys(request)
        if enabled and any(count(keys[name]) >= limit for name, limit, _period in self.LIMITS):
            return render(request, "429.html", status=429)
        response = super().post(request, *args, **kwargs)
        if enabled:
            if request.user.is_authenticated:
                reset(keys["acct-ip"])
            else:
                for name, _limit, period in self.LIMITS:
                    incr(keys[name], period)
        return response


@login_required
def account(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Changes saved."))
        return redirect("accounts:account")
    return render(request, "accounts/account.html", {"form": form})


def profile(request, display_name):
    from apps.catalog.models import Entry

    member = get_object_or_404(User, display_name=display_name, is_active=True)
    qs = Entry.objects.published().filter(author=member).select_related("car_model__make", "author").with_stats()
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/profile.html",
        {"member": member, "page": page, "entry_count": page.paginator.count, "reputation": member.reputation},
    )


@login_required
def export_data(request):
    """GDPR art. 15/20: machine-readable export of everything we store about the user."""
    from apps.catalog.models import CarSuggestion, Report

    u = request.user
    sub = getattr(u, "subscription", None)
    iso = lambda d: d and d.isoformat()  # noqa: E731
    data = {
        "account": {
            "email": u.email,
            "display_name": u.display_name,
            "bio": u.bio,
            "preferred_language": u.preferred_language,
            "notify_comments": u.notify_comments,
            "date_joined": iso(u.date_joined),
            "last_login": iso(u.last_login),
            "terms_accepted_at": iso(u.terms_accepted_at),
            "privacy_accepted_at": iso(u.privacy_accepted_at),
            "marketing_consent": u.marketing_consent,
        },
        "subscription": sub and {
            "status": sub.status,
            "current_period_end": iso(sub.current_period_end),
            "cancel_at_period_end": sub.cancel_at_period_end,
        },
        "entries": [
            {
                "title": e.title,
                "car": str(e.car_model),
                "category": e.category,
                "body": e.body,
                "parameters": [{"name": p.name, "value": p.value, "unit": p.unit} for p in e.parameters.all()],
                "attachments": [a.original_name for a in e.attachments.all()],
                "created_at": iso(e.created_at),
            }
            for e in u.entries.select_related("car_model__make").prefetch_related("parameters", "attachments")
        ],
        "comments": [{"entry": c.entry.title, "body": c.body, "created_at": iso(c.created_at)} for c in u.comments.select_related("entry")],
        "votes": [v.entry.title for v in u.votes.select_related("entry")],
        "bookmarks": [b.entry.title for b in u.bookmarks.select_related("entry")],
        "reports": [
            {"entry": r.entry.title, "reason": r.reason, "created_at": iso(r.created_at), "resolved": r.resolved}
            for r in Report.objects.filter(reporter=u).select_related("entry")
        ],
        "car_suggestions": [
            {"car": str(s), "created_at": iso(s.created_at)} for s in CarSuggestion.objects.filter(user=u)
        ],
    }
    resp = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json")
    resp["Content-Disposition"] = 'attachment; filename="my-data.json"'
    resp["Cache-Control"] = "private, no-store"
    return resp


@login_required
def delete_account(request):
    """GDPR art. 17. Cancels the Stripe subscription, then erases the account.
    Authored entries/comments are kept but detached from the person (author -> NULL)."""
    form = DeleteAccountForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        from apps.billing.services import cancel_subscription_immediately

        user = request.user
        cancel_subscription_immediately(user)
        logout(request)
        user.delete()
        messages.success(request, _("Your account has been deleted."))
        return redirect("core:landing")
    return render(request, "accounts/delete.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("core:landing")


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """A completed reset proves control of the mailbox, so it also confirms the email address.
    This is how the real owner takes over an address someone else registered first."""

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if not user.email_verified:
            User.objects.filter(pk=user.pk).update(email_verified=True)
        return response


password_reset_ratelimit = method_decorator(ratelimit("password-reset", limit=5, period=3600), name="dispatch")
