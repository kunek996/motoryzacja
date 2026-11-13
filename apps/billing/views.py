import json
import logging
from datetime import timedelta

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.ratelimit import ratelimit

from . import services
from .models import StripeEvent, Subscription

log = logging.getLogger(__name__)


def pricing(request):
    return render(request, "billing/pricing.html", {"dev_mode": services.dev_mode()})


@login_required
@require_POST
@ratelimit("checkout", limit=10, period=600, by="user")
def checkout(request):
    if request.user.has_access and not request.user.is_staff:
        return redirect("billing:manage")
    if not request.user.email_verified:
        messages.error(request, _("Confirm your email address first."))
        return redirect("billing:pricing")
    if not services.configured():
        messages.error(request, _("Payments are not configured yet. Please try again later."))
        return redirect("billing:pricing")
    existing = Subscription.objects.filter(user=request.user).first()
    if existing and existing.stripe_subscription_id and existing.status in ("past_due", "unpaid"):
        # Fix the payment of the existing subscription instead of starting a second one.
        messages.info(request, _("Your last payment failed. Please update your payment method in the billing portal."))
        return redirect("billing:manage")
    base = settings.SITE_URL.rstrip("/")
    try:
        url = services.create_checkout_url(
            request.user,
            success_url=base + reverse("billing:success"),
            cancel_url=base + reverse("billing:pricing"),
        )
    except stripe.StripeError:
        log.exception("Stripe checkout failed for user %s", request.user.pk)
        messages.error(request, _("The payment provider is temporarily unavailable. Please try again."))
        return redirect("billing:pricing")
    return redirect(url)


@login_required
def success(request):
    # Access is granted by the webhook, not by this page (it can be forged/opened manually).
    return render(request, "billing/success.html")


@login_required
@require_POST
def portal(request):
    if not services.configured():
        messages.error(request, _("Payments are not configured yet. Please try again later."))
        return redirect("billing:manage")
    try:
        url = services.create_portal_url(
            request.user, return_url=settings.SITE_URL.rstrip("/") + reverse("accounts:account")
        )
    except stripe.StripeError:
        log.exception("Stripe portal failed for user %s", request.user.pk)
        messages.error(request, _("The payment provider is temporarily unavailable. Please try again."))
        return redirect("billing:manage")
    return redirect(url)


@login_required
def manage(request):
    return render(request, "billing/manage.html", {"dev_mode": services.dev_mode()})


# --- Local development only: simulate a subscription without Stripe ----------------------

@login_required
@require_POST
def dev_activate(request):
    if not services.dev_mode():
        raise Http404
    Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            "stripe_customer_id": f"dev_cus_{request.user.pk}",
            "stripe_subscription_id": f"dev_sub_{request.user.pk}",
            "status": "active",
            "current_period_end": timezone.now() + timedelta(days=30),
            "cancel_at_period_end": False,
        },
    )
    messages.success(request, _("Test subscription activated (development mode)."))
    return redirect("catalog:home")


@login_required
@require_POST
def dev_cancel(request):
    if not services.dev_mode():
        raise Http404
    Subscription.objects.filter(user=request.user).update(status="canceled")
    messages.info(request, _("Test subscription cancelled (development mode)."))
    return redirect("billing:pricing")


# --- Stripe webhook --------------------------------------------------------------------------

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("webhook not configured")
    try:
        stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)  # verifies signature
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponseBadRequest("invalid signature")

    event = json.loads(payload)  # plain dicts from here on
    try:
        with transaction.atomic():
            StripeEvent.objects.create(event_id=event["id"], type=event["type"])
            _handle(event)
    except IntegrityError:
        pass  # already processed (Stripe retries) -> idempotent 200
    return HttpResponse(status=200)


SUBSCRIPTION_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "customer.subscription.paused",
    "customer.subscription.resumed",
}


def _handle(event):
    obj = event["data"]["object"]
    etype = event["type"]
    if etype in SUBSCRIPTION_EVENTS:
        # Events can arrive out of order: re-read the current state from Stripe when possible.
        services.sync_subscription(services.fresh_subscription(obj["id"]) or obj)
    elif etype == "checkout.session.completed" and obj.get("mode") == "subscription" and obj.get("subscription"):
        sub = services.fresh_subscription(obj["subscription"])
        if sub:
            services.sync_subscription(sub)
    # invoice.payment_failed: Stripe moves the subscription to past_due/unpaid and
    # sends customer.subscription.updated, which revokes access above.
