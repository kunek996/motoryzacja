"""Shared helpers for the test suites."""
import shutil
import tempfile

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.billing.models import Subscription
from apps.catalog.models import CarModel, Entry, Make

PASSWORD = "S3cure-pass-123"


def make_user(email="a@example.com", name="alice", paid=False, **kw):
    kw.setdefault("email_verified", True)
    u = User.objects.create_user(email, PASSWORD, display_name=name, **kw)
    if paid:
        Subscription.objects.create(user=u, stripe_customer_id=f"cus_{name}", status="active")
    return User.objects.get(pk=u.pk)


def make_car(make="BMW", model="335i", gen="E92"):
    mk, _ = Make.objects.get_or_create(name=make, defaults={"slug": make.lower()})
    car, _ = CarModel.objects.get_or_create(make=mk, name=model, generation=gen)
    return car


def make_entry(author=None, title="Stage 1", body="secret map data", car=None, **kw):
    return Entry.objects.create(
        author=author, car_model=car or make_car(), category=kw.pop("category", "ecu"), title=title, body=body, **kw
    )


class BaseTestCase(TestCase):
    """Fresh cache (rate limits) and a throw-away private media folder per test class."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp()
        cls._media_override = override_settings(PRIVATE_MEDIA_ROOT=cls._media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)

    def setUp(self):
        cache.clear()
