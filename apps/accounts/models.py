from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

nickname_validator = RegexValidator(
    r"^[A-Za-z0-9_.-]{3,30}$",
    _("Use 3–30 characters: letters, digits, dot, dash or underscore."),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, email_verified=True)
        return self._create(email, password, **extra)


class User(AbstractUser):
    """Email-based login. Data kept to the minimum needed (GDPR data minimisation)."""

    username = None
    email = models.EmailField(_("email"), unique=True)
    display_name = models.CharField(
        _("nickname"),
        max_length=30,
        unique=True,
        validators=[nickname_validator],
        help_text=_("3–30 characters: letters, digits, dot, dash, underscore. Visible publicly."),
    )
    bio = models.CharField(_("about me"), max_length=300, blank=True)
    email_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=5, default="pl")
    notify_comments = models.BooleanField(_("email me about comments on my entries"), default=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]
    objects = UserManager()

    # Real name is not collected.
    first_name = None
    last_name = None

    def __str__(self):
        return self.display_name

    def get_full_name(self):
        return self.display_name

    def get_short_name(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("accounts:profile", args=[self.display_name])

    @property
    def reputation(self) -> int:
        """Helpful votes received on published entries."""
        from apps.catalog.models import Entry, Vote

        return Vote.objects.filter(entry__author=self, entry__status=Entry.Status.PUBLISHED).count()

    @property
    def has_access(self) -> bool:
        """True when the user may see paid content (staff always can)."""
        if self.is_staff:
            return True
        sub = getattr(self, "subscription", None)
        return bool(sub and sub.is_active)
