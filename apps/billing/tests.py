import hashlib
import hmac
import json
import time
from unittest import mock

from django.test import override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.core.testing import BaseTestCase, make_user

from . import services
from .models import StripeEvent, Subscription

SECRET = "whsec_test"


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET, STRIPE_SECRET_KEY="")
class WebhookTests(BaseTestCase):
    def _post(self, payload: dict, secret=SECRET):
        body = json.dumps(payload)
        ts = str(int(time.time()))
        sig = hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
        return self.client.post(
            reverse("stripe_webhook"), body, content_type="application/json", HTTP_STRIPE_SIGNATURE=f"t={ts},v1={sig}"
        )

    def _event(self, status="active", eid="evt_1"):
        return {
            "id": eid, "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_1", "customer": "cus_alice", "status": status,
                                "cancel_at_period_end": False, "current_period_end": int(time.time()) + 86400}},
        }

    def test_rejects_bad_signature(self):
        self.assertEqual(self._post(self._event(), secret="wrong").status_code, 400)

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_rejects_when_not_configured(self):
        self.assertEqual(self._post(self._event()).status_code, 400)

    def test_activates_then_revokes_access_and_is_idempotent(self):
        u = make_user()
        Subscription.objects.create(user=u, stripe_customer_id="cus_alice")
        self.assertEqual(self._post(self._event("active")).status_code, 200)
        self.assertTrue(User.objects.get(pk=u.pk).has_access)
        self.assertEqual(self._post(self._event("canceled")).status_code, 200)  # replayed id
        self.assertTrue(User.objects.get(pk=u.pk).has_access)
        self.assertEqual(StripeEvent.objects.count(), 1)
        self._post(self._event("canceled", eid="evt_2"))
        self.assertFalse(User.objects.get(pk=u.pk).has_access)

    def test_old_subscription_event_does_not_revoke_newer_paid_one(self):
        u = make_user()
        Subscription.objects.create(user=u, stripe_customer_id="cus_alice")
        new = self._event("active", eid="evt_new")
        new["data"]["object"]["id"] = "sub_B"
        self._post(new)
        old = self._event("canceled", eid="evt_old")
        old["type"] = "customer.subscription.deleted"
        old["data"]["object"]["id"] = "sub_A"
        self._post(old)
        s = Subscription.objects.get()
        self.assertEqual((s.stripe_subscription_id, s.status), ("sub_B", "active"))

    def test_period_end_from_subscription_items(self):
        u = make_user()
        Subscription.objects.create(user=u, stripe_customer_id="cus_alice")
        services.sync_subscription({"id": "sub_9", "customer": "cus_alice", "status": "active",
                                    "items": {"data": [{"current_period_end": 1893456000}]}})
        self.assertEqual(Subscription.objects.get().current_period_end.year, 2030)


class CheckoutTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.client.force_login(self.user)

    @override_settings(STRIPE_SECRET_KEY="", STRIPE_PRICE_ID="")
    def test_checkout_without_configuration_shows_error(self):
        r = self.client.post(reverse("billing:checkout"))
        self.assertRedirects(r, reverse("billing:pricing"))

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PRICE_ID="price_x")
    def test_checkout_redirects_to_stripe(self):
        with mock.patch.object(services, "create_checkout_url", return_value="https://checkout.stripe.com/c/pay/x") as m:
            r = self.client.post(reverse("billing:checkout"))
        self.assertEqual(r.url, "https://checkout.stripe.com/c/pay/x")
        self.assertTrue(m.call_args.kwargs["success_url"].endswith(reverse("billing:success")))

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PRICE_ID="price_x")
    def test_unverified_user_cannot_checkout(self):
        User.objects.filter(pk=self.user.pk).update(email_verified=False)
        with mock.patch.object(services, "create_checkout_url") as m:
            self.client.post(reverse("billing:checkout"))
        m.assert_not_called()

    @override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_PRICE_ID="price_x")
    def test_past_due_user_is_sent_to_portal_not_new_checkout(self):
        Subscription.objects.create(user=self.user, stripe_customer_id="cus_x", stripe_subscription_id="sub_x", status="past_due")
        with mock.patch.object(services, "create_checkout_url") as m:
            r = self.client.post(reverse("billing:checkout"))
        m.assert_not_called()
        self.assertRedirects(r, reverse("billing:manage"))

    @override_settings(STRIPE_SECRET_KEY="sk_test_x")
    def test_account_deletion_cancels_all_live_subscriptions(self):
        Subscription.objects.create(user=self.user, stripe_customer_id="cus_x", stripe_subscription_id="", status="incomplete")
        listed = [{"id": "sub_1", "status": "active"}, {"id": "sub_2", "status": "canceled"}]
        with mock.patch.object(services, "customer_subscriptions", return_value=listed), \
                mock.patch.object(services.stripe.Subscription, "cancel") as cancel:
            services.cancel_subscription_immediately(self.user)
        cancel.assert_called_once_with("sub_1")

    def test_checkout_requires_post(self):
        self.assertEqual(self.client.get(reverse("billing:checkout")).status_code, 405)


class DevModeTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user()
        self.client.force_login(self.user)

    @override_settings(DEBUG=True, STRIPE_SECRET_KEY="", STRIPE_PRICE_ID="")
    def test_simulated_subscription_in_development(self):
        self.client.post(reverse("billing:dev_activate"))
        self.assertTrue(User.objects.get(pk=self.user.pk).has_access)
        self.client.post(reverse("billing:dev_cancel"))
        self.assertFalse(User.objects.get(pk=self.user.pk).has_access)

    @override_settings(DEBUG=False)
    def test_simulation_disabled_in_production(self):
        self.assertEqual(self.client.post(reverse("billing:dev_activate")).status_code, 404)
        self.assertFalse(User.objects.get(pk=self.user.pk).has_access)

    @override_settings(DEBUG=True, STRIPE_SECRET_KEY="sk_test_x", STRIPE_PRICE_ID="price_x")
    def test_simulation_disabled_when_stripe_configured(self):
        self.assertEqual(self.client.post(reverse("billing:dev_activate")).status_code, 404)
