from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    ACTIVE_STATUSES = {"active", "trialing"}

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    stripe_customer_id = models.CharField(max_length=64, unique=True)
    stripe_subscription_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32, default="incomplete")
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} [{self.status}]"

    @property
    def is_active(self) -> bool:
        if self.status in self.ACTIVE_STATUSES:
            return True
        # Canceled-at-period-end subs stay "active" in Stripe until the end, so no extra case needed.
        return False


class StripeEvent(models.Model):
    """Processed webhook events: makes the webhook idempotent."""

    event_id = models.CharField(max_length=80, unique=True)
    type = models.CharField(max_length=100)
    received_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type} {self.event_id}"
