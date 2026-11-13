"""Stripe integration. Stripe is the source of truth; we mirror status via webhooks."""
import logging
from datetime import datetime, timezone as dt_tz

import stripe
from django.conf import settings
from django.db import transaction

from .models import Subscription

log = logging.getLogger(__name__)


DEV_PREFIX = "dev_"


def configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PRICE_ID)


def dev_mode() -> bool:
    """Local development without Stripe keys: allow a simulated subscription."""
    return settings.DEBUG and not configured()


def _client():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _to_dict(obj) -> dict:
    return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)


def fresh_subscription(subscription_id: str):
    """Current subscription state straight from Stripe (None when Stripe is not configured)."""
    if not settings.STRIPE_SECRET_KEY:
        return None
    return _to_dict(_client().Subscription.retrieve(subscription_id))


def get_or_create_customer(user) -> Subscription:
    """One Stripe customer per user, safe against double-submitted checkouts:
    the user row is locked while we look up / create, and Stripe gets an idempotency key."""
    from apps.accounts.models import User

    with transaction.atomic():
        User.objects.select_for_update().filter(pk=user.pk).first()
        sub = Subscription.objects.filter(user=user).first()
        if sub and not sub.stripe_customer_id.startswith(DEV_PREFIX):
            return sub
        customer = _client().Customer.create(
            email=user.email,
            metadata={"user_id": str(user.pk)},
            preferred_locales=[user.preferred_language],
            idempotency_key=f"tunehub-customer-{user.pk}-{sub.pk if sub else 'new'}",
        )
        if sub:  # replace a simulated development customer with a real one
            sub.stripe_customer_id, sub.stripe_subscription_id, sub.status = customer["id"], "", "incomplete"
            sub.save()
            return sub
        return Subscription.objects.create(user=user, stripe_customer_id=customer["id"])


def customer_subscriptions(customer_id: str) -> list:
    """All subscriptions of a customer (any status), or [] without Stripe access."""
    if not settings.STRIPE_SECRET_KEY or customer_id.startswith(DEV_PREFIX):
        return []
    result = _client().Subscription.list(customer=customer_id, status="all", limit=20)
    return [_to_dict(s) for s in result.data]


def create_checkout_url(user, success_url: str, cancel_url: str) -> str:
    sub = get_or_create_customer(user)
    params = dict(
        mode="subscription",
        customer=sub.stripe_customer_id,
        client_reference_id=str(user.pk),
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        billing_address_collection="required",  # needed for correct VAT
        tax_id_collection={"enabled": True},  # B2B VAT ID
        customer_update={"address": "auto", "name": "auto"},
        locale=user.preferred_language if user.preferred_language in {"pl", "en", "de"} else "auto",
        allow_promotion_codes=True,
    )
    if settings.STRIPE_AUTOMATIC_TAX:
        params["automatic_tax"] = {"enabled": True}
    session = _client().checkout.Session.create(**params)
    return session["url"]


def create_portal_url(user, return_url: str) -> str:
    sub = get_or_create_customer(user)
    session = _client().billing_portal.Session.create(customer=sub.stripe_customer_id, return_url=return_url)
    return session["url"]


def _period_end(stripe_sub: dict):
    ts = stripe_sub.get("current_period_end")
    if ts is None:  # newer Stripe API versions keep it on the subscription item
        items = (stripe_sub.get("items") or {}).get("data") or []
        ts = items[0].get("current_period_end") if items else None
    return datetime.fromtimestamp(ts, tz=dt_tz.utc) if ts else None


# Which subscription "wins" when a customer has several (e.g. an old past_due one and a new paid one).
_STATUS_RANK = {"active": 3, "trialing": 3, "past_due": 2, "unpaid": 1, "paused": 1, "incomplete": 0}


def _rank(stripe_sub: dict):
    end = _period_end(stripe_sub)
    return (_STATUS_RANK.get(stripe_sub.get("status"), 0), end.timestamp() if end else 0)


def sync_subscription(stripe_sub: dict) -> None:
    """Mirror the customer's access state. The customer may have several subscriptions, so the
    stored row reflects the BEST one, not simply the subscription the event was about."""
    sub = Subscription.objects.filter(stripe_customer_id=stripe_sub["customer"]).first()
    if not sub:
        log.warning("Webhook for unknown customer %s", stripe_sub["customer"])
        return
    listed = customer_subscriptions(sub.stripe_customer_id)
    best = max(listed or [stripe_sub], key=_rank)
    if not listed:
        # No API access: never let an event about ANOTHER, worse subscription override the stored one.
        stored = {"status": sub.status, "current_period_end": sub.current_period_end and int(sub.current_period_end.timestamp())}
        if sub.stripe_subscription_id and sub.stripe_subscription_id != best["id"] and _rank(stored) > _rank(best):
            return
    sub.stripe_subscription_id = best["id"]
    sub.status = best["status"]
    sub.current_period_end = _period_end(best)
    sub.cancel_at_period_end = bool(best.get("cancel_at_period_end"))
    sub.save()


def cancel_subscription_immediately(user) -> None:
    """Used on account deletion: cancel EVERY live subscription of the customer (also one whose
    webhook has not arrived yet). Best effort: never blocks the erasure.
    The Stripe customer record itself is kept: invoices must be retained for tax purposes."""
    sub = Subscription.objects.filter(user=user).first()
    if not sub or not settings.STRIPE_SECRET_KEY or sub.stripe_customer_id.startswith(DEV_PREFIX):
        return
    try:
        ids = {s["id"] for s in customer_subscriptions(sub.stripe_customer_id) if s.get("status") not in ("canceled", "incomplete_expired")}
        if sub.stripe_subscription_id and not sub.stripe_subscription_id.startswith(DEV_PREFIX):
            ids.add(sub.stripe_subscription_id)
        for sid in ids:
            try:
                _client().Subscription.cancel(sid)
            except stripe.InvalidRequestError:  # already canceled
                pass
    except Exception:  # noqa: BLE001
        log.exception("Could not cancel Stripe subscriptions of customer %s", sub.stripe_customer_id)
