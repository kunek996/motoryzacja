from django.conf import settings
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from apps.accounts.models import User
from apps.catalog.models import Entry, Make


def landing(request):
    published = Entry.objects.published()
    latest = published.select_related("car_model__make", "author").with_stats().order_by("-created_at")[:6]
    top_makes = (
        Make.objects.annotate(n=Count("models__entries", filter=Q(models__entries__status=Entry.Status.PUBLISHED)))
        .filter(n__gt=0)
        .order_by("-n", "name")[:8]
    )
    stats = {
        "entries": published.count(),
        "makes": Make.objects.count(),
        "members": User.objects.filter(is_active=True, email_verified=True).count(),
    }
    return render(request, "core/landing.html", {"latest": latest, "top_makes": top_makes, "stats": stats})


def terms(request):
    return render(request, "core/terms.html")


def privacy(request):
    return render(request, "core/privacy.html")


@require_GET
def healthz(request):
    """Liveness/readiness probe for the load balancer / container orchestrator."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:  # noqa: BLE001
        return JsonResponse({"status": "error", "db": False}, status=503)
    return JsonResponse({"status": "ok", "db": True})


@require_GET
@cache_page(60 * 60)
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /*/accounts/",
        "Disallow: /*/billing/",
        # The admin path is intentionally NOT listed (it is secret); admin pages are noindex anyway.
        "Disallow: /*/entries/new/",
        "Disallow: /*/entries/saved/",
        "Disallow: /*/entries/mine/",
        "Disallow: /*/entries/api/",
        "Disallow: /*/entries/attachment/",
        f"Sitemap: {settings.SITE_URL.rstrip('/')}{reverse('sitemap')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def csrf_failure(request, reason=""):
    return render(request, "403_csrf.html", status=403)
