import json
import re

from django.core import mail
from django.urls import reverse

from apps.core.testing import PASSWORD, BaseTestCase, make_entry, make_user

from .models import User

SIGNUP = {"email": "N@Example.com", "display_name": "newbie", "password1": "Str0ng-pass-99x", "password2": "Str0ng-pass-99x"}


class SignupTests(BaseTestCase):
    def test_signup_requires_consents_and_verification(self):
        self.assertEqual(self.client.post(reverse("accounts:signup"), SIGNUP).status_code, 200)  # no consents
        self.assertFalse(User.objects.exists())
        self.client.post(reverse("accounts:signup"), {**SIGNUP, "accept_terms": "on", "accept_privacy": "on"})
        u = User.objects.get(email="n@example.com")
        self.assertFalse(u.email_verified)
        self.assertIsNotNone(u.terms_accepted_at)
        self.assertTrue(u.password.startswith("argon2"))
        self.assertEqual(len(mail.outbox), 1)
        # cannot log in before verification
        r = self.client.post(reverse("accounts:login"), {"username": "n@example.com", "password": SIGNUP["password1"]})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        # verification link confirms the address but never logs anyone in (no login CSRF / takeover)
        link = next(line for line in mail.outbox[0].body.splitlines() if "/accounts/verify/" in line)
        r = self.client.get(link[link.index("/pl/"):])
        self.assertRedirects(r, reverse("accounts:login"))
        u.refresh_from_db()
        self.assertTrue(u.email_verified)
        self.assertNotIn("_auth_user_id", self.client.session)
        # now the password login works
        self.client.post(reverse("accounts:login"), {"username": "n@example.com", "password": SIGNUP["password1"]})
        self.assertIn("_auth_user_id", self.client.session)

    def test_password_reset_confirms_email_of_preregistered_account(self):
        """Someone registered the victim's address with their own password: the owner resets it."""
        squatter = make_user("victim@example.com", "squatter", email_verified=False)
        self.client.post(reverse("accounts:password_reset"), {"email": "victim@example.com"})
        link = next(line for line in mail.outbox[-1].body.splitlines() if "/password/reset/" in line)
        r = self.client.get(link[link.index("/pl/"):], follow=True)
        new_pw = "Brand-new-pass-77"
        self.client.post(r.redirect_chain[-1][0], {"new_password1": new_pw, "new_password2": new_pw})
        squatter.refresh_from_db()
        self.assertTrue(squatter.email_verified)
        self.assertTrue(squatter.check_password(new_pw))
        self.assertFalse(squatter.check_password(PASSWORD))  # the squatter's password no longer works

    def test_tampered_verification_token_rejected(self):
        r = self.client.get(reverse("accounts:verify", args=["bogus:token"]))
        self.assertRedirects(r, reverse("accounts:login"))

    def test_nickname_rules(self):
        make_user("x@example.com", "Taken")
        data = {**SIGNUP, "accept_terms": "on", "accept_privacy": "on"}
        r = self.client.post(reverse("accounts:signup"), {**data, "display_name": "taken"})
        self.assertIn("display_name", r.context["form"].errors)
        r = self.client.post(reverse("accounts:signup"), {**data, "display_name": "bad name!"})
        self.assertIn("display_name", r.context["form"].errors)

    def test_resend_verification_does_not_leak_accounts(self):
        make_user("u@example.com", "unverified", email_verified=False)
        r1 = self.client.post(reverse("accounts:resend_verification"), {"email": "u@example.com"})
        r2 = self.client.post(reverse("accounts:resend_verification"), {"email": "nobody@example.com"})
        strip = lambda r: re.sub(rb'value="[^"]{40,}"', b"", r.content)  # noqa: E731 – drop per-response CSRF token
        self.assertEqual(strip(r1), strip(r2))
        self.assertEqual(len(mail.outbox), 1)

    def test_signup_rate_limited(self):
        codes = [self.client.post(reverse("accounts:signup"), {}).status_code for _ in range(7)]
        self.assertEqual(codes[-1], 429)


class LoginTests(BaseTestCase):
    def test_login_case_insensitive_email(self):
        make_user("a@example.com", "alice")
        self.client.post(reverse("accounts:login"), {"username": "A@Example.com", "password": PASSWORD})
        self.assertIn("_auth_user_id", self.client.session)

    def test_brute_force_is_throttled(self):
        make_user("a@example.com", "alice")
        codes = [
            self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": "wrong"}).status_code
            for _ in range(10)
        ]
        self.assertEqual(codes[-1], 429)
        # even the right password is refused while throttled (from this IP)
        r = self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 429)

    def test_attacker_cannot_lock_out_owner_from_another_ip(self):
        make_user("a@example.com", "alice")
        for _ in range(10):
            self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": "x"}, REMOTE_ADDR="6.6.6.6")
        self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": PASSWORD}, REMOTE_ADDR="10.1.1.1")
        self.assertIn("_auth_user_id", self.client.session)

    def test_successful_logins_do_not_count(self):
        make_user("a@example.com", "alice")
        for _ in range(12):
            self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": PASSWORD})
            self.client.logout()
        r = self.client.post(reverse("accounts:login"), {"username": "a@example.com", "password": PASSWORD})
        self.assertEqual(r.status_code, 302)


class AccountTests(BaseTestCase):
    def test_profile_page_and_settings(self):
        u = make_user(paid=True)
        make_entry(u, title="Public teaser")
        r = self.client.get(reverse("accounts:profile", args=["alice"]))
        self.assertContains(r, "Public teaser")
        self.assertEqual(self.client.get(reverse("accounts:profile", args=["ghost"])).status_code, 404)
        self.client.force_login(u)
        self.client.post(reverse("accounts:account"), {"display_name": "alice2", "bio": "hi", "preferred_language": "de", "notify_comments": ""})
        u.refresh_from_db()
        self.assertEqual((u.display_name, u.preferred_language, u.notify_comments), ("alice2", "de", False))

    def test_export_contains_only_own_data(self):
        a, b = make_user("a@example.com", "alice"), make_user("b@example.com", "bob")
        make_entry(a)
        self.client.force_login(b)
        data = json.loads(self.client.get(reverse("accounts:export")).content)
        self.assertEqual(data["account"]["email"], "b@example.com")
        self.assertEqual(data["entries"], [])
        self.assertIn("votes", data)

    def test_delete_account_keeps_content_anonymised(self):
        u = make_user(paid=True)
        entry = make_entry(u)
        self.client.force_login(u)
        self.client.post(reverse("accounts:delete"), {"password": "wrong"})
        self.assertTrue(User.objects.filter(pk=u.pk).exists())
        self.client.post(reverse("accounts:delete"), {"password": PASSWORD})
        self.assertFalse(User.objects.filter(pk=u.pk).exists())
        entry.refresh_from_db()
        self.assertIsNone(entry.author)
        self.assertEqual(self.client.get(entry.get_absolute_url()).status_code, 200)
