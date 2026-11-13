from django.contrib import admin

from .models import StripeEvent, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "current_period_end", "cancel_at_period_end")
    list_filter = ("status",)
    search_fields = ("user__email", "stripe_customer_id")
    readonly_fields = ("stripe_customer_id", "stripe_subscription_id")


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "type", "received_at")
