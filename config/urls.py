from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.billing.views import stripe_webhook
from apps.core.sitemaps import SITEMAPS
from apps.core.views import healthz, robots_txt

admin.site.site_header = "TuneHub – moderation"
admin.site.site_title = "TuneHub admin"

# Not language-prefixed: endpoints called by external services / crawlers / language switcher.
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("billing/webhook/stripe/", stripe_webhook, name="stripe_webhook"),
    path("healthz", healthz, name="healthz"),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
]

urlpatterns += i18n_patterns(
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("entries/", include("apps.catalog.urls")),
    path("billing/", include("apps.billing.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    prefix_default_language=True,
)
