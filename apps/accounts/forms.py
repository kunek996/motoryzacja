from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


def _nickname_taken(name, exclude_pk=None):
    qs = User.objects.filter(display_name__iexact=name)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


class SignupForm(BaseUserCreationForm):
    accept_terms = forms.BooleanField(label=_("I accept the Terms of Service"))
    accept_privacy = forms.BooleanField(label=_("I have read the Privacy Policy"))
    marketing_consent = forms.BooleanField(
        required=False, label=_("I agree to receive product news by email (optional)")
    )

    class Meta:
        model = User
        fields = ("email", "display_name")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            # Point the real owner to password reset: it confirms the address and replaces any
            # password set by whoever registered it first.
            raise forms.ValidationError(
                _("An account with this email already exists. If it is yours, log in or reset your password.")
            )
        return email

    def clean_display_name(self):
        name = self.cleaned_data["display_name"]
        if _nickname_taken(name):
            raise forms.ValidationError(_("This nickname is already taken."))
        return name


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].lower()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.email_verified:
            raise forms.ValidationError(
                _("Please confirm your email address first (check your inbox)."),
                code="unverified",
            )


class ProfileForm(forms.ModelForm):
    preferred_language = forms.ChoiceField(label=_("Language for emails"), choices=settings.LANGUAGES)

    class Meta:
        model = User
        fields = ("display_name", "bio", "preferred_language", "notify_comments", "marketing_consent")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}
        labels = {"marketing_consent": _("I agree to receive product news by email (optional)")}

    def clean_display_name(self):
        name = self.cleaned_data["display_name"]
        if _nickname_taken(name, exclude_pk=self.instance.pk):
            raise forms.ValidationError(_("This nickname is already taken."))
        return name


class ResendVerificationForm(forms.Form):
    email = forms.EmailField(label=_("Email"))


class DeleteAccountForm(forms.Form):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        pw = self.cleaned_data["password"]
        if not self.user.check_password(pw):
            raise forms.ValidationError(_("Incorrect password."))
        return pw
