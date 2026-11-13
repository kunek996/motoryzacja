from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Entry


class StaticSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = True
    changefreq = "weekly"

    def items(self):
        return ["core:landing", "billing:pricing", "catalog:home", "catalog:makes", "core:terms", "core:privacy"]

    def location(self, item):
        return reverse(item)


class EntrySitemap(Sitemap):
    """Public teaser pages of published entries (full content is behind the paywall)."""

    i18n = True
    alternates = True
    changefreq = "weekly"
    limit = 5000

    def items(self):
        return Entry.objects.published().order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"static": StaticSitemap, "entries": EntrySitemap}
