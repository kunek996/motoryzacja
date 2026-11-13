import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def private_storage():
    """Callable storage (keeps machine-specific paths out of migrations).
    Files live outside any publicly served directory."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)


def attachment_path(instance, filename):
    # Random name on disk; the original name is kept in the DB only (no path traversal, no guessing).
    return f"attachments/{uuid.uuid4().hex}"


class Make(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=80)
    generation = models.CharField(max_length=40, blank=True, help_text="e.g. B8, E46, MK7")
    year_from = models.PositiveSmallIntegerField(null=True, blank=True)
    year_to = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["make__name", "name", "generation"]
        constraints = [
            models.UniqueConstraint(fields=["make", "name", "generation"], name="uniq_car_model"),
        ]

    def __str__(self):
        return " ".join(p for p in (self.make.name, self.name, self.generation) if p)

    @property
    def years(self) -> str:
        if not self.year_from:
            return ""
        return f"{self.year_from}–{self.year_to or ''}"


class EntryQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Entry.Status.PUBLISHED)

    def with_stats(self):
        """Vote/comment counts via correlated subqueries (no votes × comments join blow-up)."""

        def counter(model):
            sub = (
                model.objects.filter(entry=models.OuterRef("pk"))
                .order_by()
                .values("entry")
                .annotate(n=models.Count("pk"))
                .values("n")
            )
            return Coalesce(models.Subquery(sub, output_field=models.IntegerField()), 0)

        return self.annotate(vote_count=counter(Vote), comment_count=counter(Comment))


class Entry(models.Model):
    class Category(models.TextChoices):
        MODIFICATION = "mod", _("Modification")
        ECU_MAP = "ecu", _("Engine map (ECU)")
        GEARBOX_MAP = "tcu", _("Gearbox map (TCU)")
        TURBO = "turbo", _("Turbocharger settings")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        PUBLISHED = "pub", _("Published")
        HIDDEN = "hid", _("Hidden by moderator")

    class Fuel(models.TextChoices):
        PETROL = "petrol", _("Petrol")
        DIESEL = "diesel", _("Diesel")
        HYBRID = "hybrid", _("Hybrid")
        LPG = "lpg", _("LPG")
        E85 = "e85", _("E85 / flex fuel")
        ELECTRIC = "ev", _("Electric")

    class Stage(models.TextChoices):
        STOCK = "0", _("Stock / reference")
        STAGE1 = "1", _("Stage 1")
        STAGE2 = "2", _("Stage 2")
        STAGE3 = "3", _("Stage 3+")
        CUSTOM = "c", _("Custom")

    class Language(models.TextChoices):
        PL = "pl", "Polski"
        EN = "en", "English"
        DE = "de", "Deutsch"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="entries"
    )
    car_model = models.ForeignKey(CarModel, on_delete=models.PROTECT, related_name="entries", verbose_name=_("car"))
    category = models.CharField(_("category"), max_length=8, choices=Category.choices, db_index=True)
    title = models.CharField(_("title"), max_length=160)
    slug = models.SlugField(max_length=170, blank=True, editable=False)
    language = models.CharField(_("content language"), max_length=2, choices=Language.choices, default=Language.PL)
    model_year = models.PositiveSmallIntegerField(
        _("model year"), null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)]
    )
    fuel = models.CharField(_("fuel"), max_length=8, choices=Fuel.choices, blank=True)
    engine = models.CharField(_("engine / code"), max_length=80, blank=True, help_text=_("e.g. 2.0 TFSI EA888 Gen3"))
    ecu_type = models.CharField(_("ECU"), max_length=80, blank=True, help_text=_("e.g. Bosch MED17.5"))
    gearbox = models.CharField(_("gearbox"), max_length=80, blank=True, help_text=_("e.g. DQ250 DSG, ZF 8HP"))
    stage = models.CharField(_("stage"), max_length=1, choices=Stage.choices, blank=True)
    turbo = models.CharField(_("turbocharger"), max_length=80, blank=True, help_text=_("e.g. IHI IS38, Garrett GTX3076R"))
    boost_bar = models.DecimalField(
        _("peak boost (bar)"), max_digits=4, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
    )
    power_before_hp = models.PositiveIntegerField(_("power before (hp)"), null=True, blank=True)
    power_after_hp = models.PositiveIntegerField(_("power after (hp)"), null=True, blank=True)
    torque_before_nm = models.PositiveIntegerField(_("torque before (Nm)"), null=True, blank=True)
    torque_after_nm = models.PositiveIntegerField(_("torque after (Nm)"), null=True, blank=True)
    body = models.TextField(_("description"), max_length=10000)
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.PUBLISHED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EntryQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "entries"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)[:170] or "entry"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"pk": self.pk, "slug": self.slug or "entry"})

    @property
    def power_gain(self):
        if self.power_before_hp and self.power_after_hp:
            return self.power_after_hp - self.power_before_hp
        return None

    @property
    def torque_gain(self):
        if self.torque_before_nm and self.torque_after_nm:
            return self.torque_after_nm - self.torque_before_nm
        return None

    def can_edit(self, user) -> bool:
        return user.is_authenticated and (user.is_staff or (self.author_id == user.pk and user.has_access))


class EntryParameter(models.Model):
    """Free-form structured settings, e.g. 'Boost target @ 4000 rpm' = '1.45' bar."""

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="parameters")
    name = models.CharField(_("parameter"), max_length=80)
    value = models.CharField(_("value"), max_length=80)
    unit = models.CharField(_("unit"), max_length=16, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "pk"]

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}".strip()


class Attachment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_path, storage=private_storage)
    original_name = models.CharField(max_length=200)
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name
    # Files are removed from disk by a post_delete signal (apps/catalog/signals.py), which also
    # runs for cascade deletes (entry deleted in the admin, bulk actions).


class Comment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="comments"
    )
    body = models.TextField(_("comment"), max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Vote(models.Model):
    """'Helpful' vote. One per user per entry; authors cannot vote for themselves."""

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["entry", "user"], name="uniq_vote")]


class Bookmark(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["entry", "user"], name="uniq_bookmark")]


class CarSuggestion(models.Model):
    """A member asks moderators to add a missing make/model to the catalogue."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    make = models.CharField(_("make"), max_length=60)
    model = models.CharField(_("model"), max_length=80)
    generation = models.CharField(_("generation / code"), max_length=40, blank=True, help_text=_("e.g. B8, E46, MK7"))
    year_from = models.PositiveSmallIntegerField(_("from year"), null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)])
    year_to = models.PositiveSmallIntegerField(_("to year"), null=True, blank=True, validators=[MinValueValidator(1950), MaxValueValidator(2100)])
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["handled", "-created_at"]

    def __str__(self):
        return " ".join(p for p in (self.make, self.model, self.generation) if p)


class Report(models.Model):
    """User report of unlawful/abusive content (DSA notice-and-action)."""

    AUTO_HIDE_THRESHOLD = 3  # distinct open reports -> entry hidden until a moderator decides

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    reason = models.TextField(_("reason"), max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["resolved", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "reporter"], condition=models.Q(resolved=False), name="uniq_open_report"
            )
        ]
