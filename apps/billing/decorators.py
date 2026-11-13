from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def subscription_required(view):
    """Paywall: login + active subscription (staff bypass)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.has_access:
            messages.info(request, _("An active subscription is required to view this content."))
            return redirect("billing:pricing")
        return view(request, *args, **kwargs)

    return wrapper
