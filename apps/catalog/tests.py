import hashlib
import os

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.core.testing import BaseTestCase, make_car, make_entry, make_user

from .models import Attachment, Bookmark, Entry, EntryParameter, Report, Vote


def mock_messages():
    """Minimal message storage so admin actions can call message_user() outside a request."""
    class _Store(list):
        def add(self, level, message, extra_tags=""):
            self.append(message)

    return _Store()


def entry_post_data(car, **extra):
    data = {
        "car_model": car.pk, "category": "ecu", "title": "My Stage 1", "language": "pl", "body": "full description",
        "params-TOTAL_FORMS": "1", "params-INITIAL_FORMS": "0", "params-MIN_NUM_FORMS": "0", "params-MAX_NUM_FORMS": "30",
        "params-0-name": "Boost", "params-0-value": "1.4", "params-0-unit": "bar",
    }
    data.update(extra)
    return data


class PaywallTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.entry = make_entry()
        EntryParameter.objects.create(entry=self.entry, name="Boost target", value="1.45", unit="bar")

    def test_list_is_public_but_hides_body(self):
        r = self.client.get(reverse("catalog:home"))
        self.assertContains(r, "Stage 1")
        self.assertNotContains(r, "secret map data")

    def test_anonymous_gets_teaser_without_paid_content(self):
        r = self.client.get(self.entry.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "paywall")
        self.assertNotContains(r, "secret map data")
        self.assertNotContains(r, "Boost target")
        self.assertContains(r, '"isAccessibleForFree": false')

    def test_registered_without_subscription_gets_teaser(self):
        self.client.force_login(make_user())
        r = self.client.get(self.entry.get_absolute_url())
        self.assertNotContains(r, "secret map data")

    def test_subscriber_sees_everything(self):
        self.client.force_login(make_user(paid=True))
        r = self.client.get(self.entry.get_absolute_url())
        self.assertContains(r, "secret map data")
        self.assertContains(r, "Boost target")

    def test_canceled_subscription_loses_access(self):
        u = make_user(paid=True)
        u.subscription.status = "canceled"
        u.subscription.save()
        self.client.force_login(u)
        self.assertNotContains(self.client.get(self.entry.get_absolute_url()), "secret map data")

    def test_hidden_entry_only_for_author_and_staff(self):
        author = make_user("au@example.com", "author", paid=True)
        e = make_entry(author, title="Hidden one", status=Entry.Status.HIDDEN)
        self.client.force_login(make_user(paid=True))
        self.assertEqual(self.client.get(e.get_absolute_url()).status_code, 404)
        self.client.force_login(author)
        self.assertEqual(self.client.get(e.get_absolute_url()).status_code, 200)
        self.assertNotContains(self.client.get(reverse("catalog:home")), "Hidden one")

    def test_short_and_wrong_slug_urls_redirect_to_canonical(self):
        r = self.client.get(reverse("catalog:detail_short", args=[self.entry.pk]))
        self.assertRedirects(r, self.entry.get_absolute_url(), status_code=301)
        r = self.client.get(reverse("catalog:detail", kwargs={"pk": self.entry.pk, "slug": "wrong"}))
        self.assertEqual(r.status_code, 301)

    def test_paid_actions_require_subscription(self):
        self.client.force_login(make_user())
        for name in ("catalog:create", "catalog:saved", "catalog:mine"):
            self.assertRedirects(self.client.get(reverse(name)), reverse("billing:pricing"), fetch_redirect_response=False)


class EntryCrudTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(paid=True)
        self.car = make_car()
        self.client.force_login(self.user)

    def test_create_with_parameters_and_attachments(self):
        files = [SimpleUploadedFile("stage1.bin", b"\x00\x01binary-map"), SimpleUploadedFile("log.csv", b"rpm,boost\n3000,1.4\n")]
        r = self.client.post(reverse("catalog:create"), {**entry_post_data(self.car), "attachments": files})
        entry = Entry.objects.get(title="My Stage 1")
        self.assertRedirects(r, entry.get_absolute_url())
        self.assertEqual(entry.author, self.user)
        self.assertEqual(entry.parameters.get().value, "1.4")
        self.assertEqual(entry.attachments.count(), 2)
        att = entry.attachments.get(original_name="stage1.bin")
        self.assertEqual(att.sha256, hashlib.sha256(b"\x00\x01binary-map").hexdigest())
        self.assertNotIn("stage1", att.file.name)  # random name on disk

    def test_rejects_disallowed_extension_and_disguised_executable(self):
        for f in (SimpleUploadedFile("evil.exe", b"hello"), SimpleUploadedFile("map.bin", b"MZ\x90\x00payload")):
            r = self.client.post(reverse("catalog:create"), {**entry_post_data(self.car), "attachments": [f]})
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.context["form"].errors.get("attachments"))
        self.assertFalse(Entry.objects.exists())

    def test_rejects_fake_image(self):
        r = self.client.post(reverse("catalog:create"), {**entry_post_data(self.car), "attachments": [SimpleUploadedFile("dyno.png", b"not an image")]})
        self.assertTrue(r.context["form"].errors.get("attachments"))

    @override_settings(ATTACHMENT_MAX_PER_ENTRY=1)
    def test_attachment_count_limit(self):
        files = [SimpleUploadedFile("a.txt", b"a"), SimpleUploadedFile("b.txt", b"b")]
        r = self.client.post(reverse("catalog:create"), {**entry_post_data(self.car), "attachments": files})
        self.assertTrue(r.context["form"].errors.get("attachments"))

    def test_unrealistic_numbers_rejected(self):
        r = self.client.post(reverse("catalog:create"), entry_post_data(self.car, power_before_hp=100, power_after_hp=900))
        self.assertIn("power_after_hp", r.context["form"].errors)

    def test_only_author_or_staff_can_edit(self):
        entry = make_entry(self.user)
        other = make_user("o@example.com", "other", paid=True)
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("catalog:edit", args=[entry.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("catalog:delete", args=[entry.pk])).status_code, 403)
        self.client.force_login(self.user)
        r = self.client.post(
            reverse("catalog:edit", args=[entry.pk]),
            entry_post_data(self.car, title="Renamed"),
        )
        entry.refresh_from_db()
        self.assertEqual(entry.title, "Renamed")
        self.assertRedirects(r, entry.get_absolute_url())
        staff = make_user("s@example.com", "staffer", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("catalog:edit", args=[entry.pk])).status_code, 200)

    def test_delete_removes_files_from_disk(self):
        self.client.post(reverse("catalog:create"), {**entry_post_data(self.car), "attachments": [SimpleUploadedFile("m.bin", b"\x00data")]})
        entry = Entry.objects.get()
        path = entry.attachments.get().file.path
        self.assertTrue(os.path.exists(path))
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("catalog:delete", args=[entry.pk]))
        self.assertFalse(Entry.objects.exists())
        self.assertFalse(os.path.exists(path))

    def test_cascade_delete_also_removes_files(self):
        entry = make_entry(self.user)
        att = Attachment(entry=entry, original_name="m.bin", size=1)
        att.file.save("x", SimpleUploadedFile("m.bin", b"\x00"))
        path = att.file.path
        with self.captureOnCommitCallbacks(execute=True):
            Entry.objects.filter(pk=entry.pk).delete()  # like the admin bulk action
        self.assertFalse(os.path.exists(path))

    def test_staff_edit_keeps_original_author(self):
        entry = make_entry(None, title="Orphan")  # author deleted their account
        staff = make_user("s@example.com", "staffer", is_staff=True)
        self.client.force_login(staff)
        self.client.post(reverse("catalog:edit", args=[entry.pk]), entry_post_data(self.car, title="Orphan fixed"))
        entry.refresh_from_db()
        self.assertEqual(entry.title, "Orphan fixed")
        self.assertIsNone(entry.author)

    def test_download_counts_and_is_private(self):
        entry = make_entry(self.user)
        att = Attachment(entry=entry, original_name="map.bin", size=3)
        att.file.save("x", SimpleUploadedFile("map.bin", b"abc"))
        r = self.client.get(reverse("catalog:download", args=[att.pk]))
        self.assertEqual(b"".join(r.streaming_content), b"abc")
        self.assertEqual(r["Content-Type"], "application/octet-stream")
        self.assertIn("no-store", r["Cache-Control"])
        att.refresh_from_db()
        self.assertEqual(att.download_count, 1)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("catalog:download", args=[att.pk])).status_code, 302)


class CommunityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.author = make_user("au@example.com", "author", paid=True)
        self.reader = make_user("re@example.com", "reader", paid=True)
        self.entry = make_entry(self.author)
        self.client.force_login(self.reader)

    def test_vote_toggle_and_reputation(self):
        url = reverse("catalog:vote", args=[self.entry.pk])
        self.client.post(url)
        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(self.author.reputation, 1)
        self.client.post(url)
        self.assertEqual(Vote.objects.count(), 0)

    def test_cannot_vote_for_own_entry(self):
        self.client.force_login(self.author)
        self.client.post(reverse("catalog:vote", args=[self.entry.pk]))
        self.assertEqual(Vote.objects.count(), 0)

    def test_bookmark_toggle_and_saved_list(self):
        self.client.post(reverse("catalog:bookmark", args=[self.entry.pk]))
        self.assertTrue(Bookmark.objects.filter(user=self.reader).exists())
        self.assertContains(self.client.get(reverse("catalog:saved")), "Stage 1")
        self.client.post(reverse("catalog:bookmark", args=[self.entry.pk]))
        self.assertFalse(Bookmark.objects.exists())

    def test_bookmark_next_rejects_external_redirect(self):
        r = self.client.post(reverse("catalog:bookmark", args=[self.entry.pk]), {"next": "//evil.example.com/"})
        self.assertEqual(r.url, self.entry.get_absolute_url())

    def test_comment_notifies_author_once(self):
        self.client.post(reverse("catalog:comment", args=[self.entry.pk]), {"body": "Nice map!"})
        self.assertEqual(self.entry.comments.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["au@example.com"])
        # author commenting on own entry -> no email; opted-out author -> no email
        self.client.force_login(self.author)
        self.client.post(reverse("catalog:comment", args=[self.entry.pk]), {"body": "Thanks"})
        self.author.notify_comments = False
        self.author.save()
        self.client.force_login(self.reader)
        self.client.post(reverse("catalog:comment", args=[self.entry.pk]), {"body": "Another"})
        self.assertEqual(len(mail.outbox), 1)

    def test_only_comment_author_can_delete(self):
        self.client.post(reverse("catalog:comment", args=[self.entry.pk]), {"body": "mine"})
        c = self.entry.comments.get()
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(reverse("catalog:comment_delete", args=[c.pk])).status_code, 403)
        self.client.force_login(self.reader)
        self.client.post(reverse("catalog:comment_delete", args=[c.pk]))
        self.assertFalse(self.entry.comments.exists())

    def test_reports_auto_hide_after_threshold_and_no_duplicates(self):
        url = reverse("catalog:report", args=[self.entry.pk])
        self.client.post(url, {"reason": "emission delete"})
        self.client.post(url, {"reason": "again"})
        self.assertEqual(Report.objects.count(), 1)
        for i in range(Report.AUTO_HIDE_THRESHOLD - 1):
            self.client.force_login(make_user(f"r{i}@example.com", f"rep{i}", paid=True))
            self.client.post(url, {"reason": "illegal"})
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.status, Entry.Status.HIDDEN)

    def test_comment_rate_limit(self):
        url = reverse("catalog:comment", args=[self.entry.pk])
        codes = [self.client.post(url, {"body": f"c{i}"}).status_code for i in range(12)]
        self.assertIn(429, codes)


class FilterTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        bmw, audi = make_car("BMW", "M3", "E46"), make_car("Audi", "S3", "8V")
        self.a = make_entry(title="BMW map", car=bmw, fuel="petrol")
        self.b = make_entry(title="Audi diesel", car=audi, fuel="diesel", category="tcu")
        self.audi = audi

    def test_filters_and_search(self):
        url = reverse("catalog:home")
        self.assertNotContains(self.client.get(url, {"make": self.audi.make_id}), "BMW map")
        self.assertContains(self.client.get(url, {"fuel": "diesel"}), "Audi diesel")
        self.assertNotContains(self.client.get(url, {"category": "tcu"}), "BMW map")
        self.assertContains(self.client.get(url, {"q": "S3"}), "Audi diesel")
        self.assertEqual(self.client.get(url, {"sort": "top", "page": "999"}).status_code, 200)

    def test_sort_by_votes(self):
        Vote.objects.create(entry=self.b, user=make_user())
        r = self.client.get(reverse("catalog:home"), {"sort": "top"})
        self.assertEqual(list(r.context["page"])[0], self.b)

    def test_models_api(self):
        r = self.client.get(reverse("catalog:api_models"), {"make": self.audi.make_id})
        self.assertEqual([m["id"] for m in r.json()["models"]], [self.audi.pk])
        self.assertEqual(self.client.get(reverse("catalog:api_models"), {"make": "x"}).json(), {"models": []})

    def test_suggest_car_and_admin_adds_it(self):
        from django.contrib.admin.sites import site

        from .admin import CarSuggestionAdmin
        from .models import CarModel, CarSuggestion

        self.client.force_login(make_user("p@example.com", "payer", paid=True))
        r = self.client.post(reverse("catalog:suggest_car"), {"make": "Alfa Romeo", "model": "Giulia", "generation": "952", "year_from": 2016})
        self.assertRedirects(r, reverse("catalog:create"))
        s = CarSuggestion.objects.get()
        request = type("R", (), {"_messages": mock_messages()})()
        CarSuggestionAdmin(CarSuggestion, site).add_to_catalogue(request, CarSuggestion.objects.all())
        self.assertTrue(CarModel.objects.filter(make__name="Alfa Romeo", name="Giulia", generation="952").exists())
        s.refresh_from_db()
        self.assertTrue(s.handled)

    def test_makes_overview(self):
        self.assertContains(self.client.get(reverse("catalog:makes")), "Audi")
