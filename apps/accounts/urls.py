from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _

from . import views
from .forms import EmailAuthenticationForm

app_name = "accounts"


@views.password_reset_ratelimit
class PasswordResetView(auth_views.PasswordResetView):
    pass


urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("verify/resend/", views.resend_verification, name="resend_verification"),
    path("verify/<str:token>/", views.verify_email, name="verify"),
    path("login/", views.LoginView.as_view(authentication_form=EmailAuthenticationForm), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.account, name="account"),
    path("export/", views.export_data, name="export"),
    path("delete/", views.delete_account, name="delete"),
    path("u/<str:display_name>/", views.profile, name="profile"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html", success_url=reverse_lazy("accounts:account"),
            extra_context={"page_title": _("Change password")},
        ),
        name="password_change",
    ),
    path(
        "password/reset/",
        PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
            extra_context={"page_title": _("Reset password"), "submit_label": _("Send reset link")},
        ),
        name="password_reset",
    ),
    path(
        "password/reset/sent/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:login"),
            extra_context={"page_title": _("Set new password")},
        ),
        name="password_reset_confirm",
    ),
]
