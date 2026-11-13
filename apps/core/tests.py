from io import StringIO

from django.core.management import CommandError, call_command
from django.test import override_settings
from django.urls import reverse

from apps.catalog.models import Entry

from .ratelimit import client_ip, hit
from .testing import BaseTestCase, make_entry


class PublicPagesTests(BaseTestCase):
    def test_pages_render_in_all_languages(self):
        make_entry()
        for lang, word in (("pl", "Biblioteka"), ("de", "Bibliothek"), ("en", "Library")):
            r = self.client.get(f"/{lang}/")
            self.assertContains(r, word)
            self.assertContains(r, 'hreflang="de"')
        for name in ("core:terms", "core:privacy", "billing:pricing", "catalog:makes", "accounts:login", "accounts:signup"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_custom_404(self):
        r = self.client.get("/pl/does-not-exist/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "404", status_code=404)


class SecurityHeadersTests(BaseTestCase):
    def test_csp_and_permissions_policy(self):
        r = self.client.get(reverse("core:landing"))
        self.assertIn("script-src 'self'", r["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])
        self.assertIn("camera=()", r["Permissions-Policy"])
        self.assertEqual(r["X-Frame-Options"], "DENY")
        self.assertNotIn("onchange=", r.content.decode())  # no inline handlers (CSP)


class InfraTests(BaseTestCase):
    def test_healthz(self):
        r = self.client.get("/healthz")
        self.assertEqual(r.json(), {"status": "ok", "db": True})

    def test_robots_and_sitemap(self):
        entry = make_entry()
        self.assertContains(self.client.get("/robots.txt"), "Sitemap:")
        r = self.client.get("/sitemap.xml")
        self.assertContains(r, entry.get_absolute_url().split("/", 2)[2])  # language-independent part
        self.assertContains(r, 'hreflang="en"')


class AdminTests(BaseTestCase):
    def test_moderation_pages_render(self):
        from apps.accounts.models import User
        from apps.catalog.models import Report

        admin = User.objects.create_superuser("root@example.com", "Adm1n-pass-xyz", display_name="root")
        entry = make_entry()
        Report.objects.create(entry=entry, reporter=admin, reason="test")
        self.client.force_login(admin)
        for model in ("catalog/entry", "catalog/report", "catalog/make", "catalog/carmodel", "catalog/comment",
                      "accounts/user", "billing/subscription"):
            url = f"/pl/admin/{model}/"
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get(f"/pl/admin/catalog/entry/{entry.pk}/change/").status_code, 200)
        self.assertEqual(self.client.get("/pl/admin/accounts/user/add/").status_code, 200)


class RateLimitTests(BaseTestCase):
    def test_hit_counts_within_window(self):
        self.assertEqual([hit("t:k", 2, 60) for _ in range(3)], [True, True, False])

    @override_settings(RATELIMIT_PROXY_COUNT=1)
    def test_client_ip_behind_one_proxy(self):
        req = type("R", (), {"META": {"REMOTE_ADDR": "10.0.0.1", "HTTP_X_FORWARDED_FOR": "6.6.6.6, 1.2.3.4"}})()
        self.assertEqual(client_ip(req), "1.2.3.4")  # spoofed left-most value ignored


class SeedDemoTests(BaseTestCase):
    @override_settings(DEBUG=True)
    def test_seed_is_idempotent(self):
        call_command("seed_demo", stdout=StringIO())
        n = Entry.objects.count()
        self.assertGreater(n, 10)
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Entry.objects.count(), n)

    @override_settings(DEBUG=False)
    def test_seed_refuses_in_production(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())
