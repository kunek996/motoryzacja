from django.contrib import admin
from django.db.models import Count, Q
from django.utils.text import slugify

from .models import Attachment, Bookmark, CarModel, CarSuggestion, Comment, Entry, EntryParameter, Make, Report, Vote


class CarModelInline(admin.TabularInline):
    model = CarModel
    extra = 1


@admin.register(Make)
class MakeAdmin(admin.ModelAdmin):
    list_display = ("name", "model_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    inlines = [CarModelInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_models=Count("models"))

    @admin.display(ordering="_models", description="Models")
    def model_count(self, obj):
        return obj._models


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ("make", "name", "generation", "year_from", "year_to")
    list_filter = ("make",)
    search_fields = ("name", "make__name", "generation")


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("original_name", "size", "sha256", "download_count")
    fields = ("original_name", "size", "sha256", "download_count")


class ParameterInline(admin.TabularInline):
    model = EntryParameter
    extra = 0


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("title", "car_model", "category", "author", "status", "open_reports", "created_at")
    list_filter = ("status", "category", "fuel", "language", "car_model__make")
    search_fields = ("title", "body", "engine", "ecu_type", "author__email", "author__display_name")
    list_select_related = ("car_model__make", "author")
    autocomplete_fields = ("car_model",)
    raw_id_fields = ("author",)
    actions = ["hide", "publish"]
    inlines = [ParameterInline, AttachmentInline]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _open_reports=Count("reports", filter=Q(reports__resolved=False))
        )

    @admin.display(ordering="_open_reports", description="Open reports")
    def open_reports(self, obj):
        return obj._open_reports

    @admin.action(description="Hide selected entries")
    def hide(self, request, qs):
        qs.update(status=Entry.Status.HIDDEN)

    @admin.action(description="Publish selected entries (and resolve their reports)")
    def publish(self, request, qs):
        qs.update(status=Entry.Status.PUBLISHED)
        Report.objects.filter(entry__in=qs).update(resolved=True)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("entry", "reporter", "short_reason", "created_at", "resolved")
    list_filter = ("resolved",)
    list_select_related = ("entry", "reporter")
    actions = ["resolve", "hide_entries"]

    @admin.display(description="Reason")
    def short_reason(self, obj):
        return obj.reason[:80]

    @admin.action(description="Mark as resolved")
    def resolve(self, request, qs):
        qs.update(resolved=True)

    @admin.action(description="Hide reported entries and resolve")
    def hide_entries(self, request, qs):
        Entry.objects.filter(reports__in=qs).update(status=Entry.Status.HIDDEN)
        qs.update(resolved=True)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("entry", "author", "created_at")
    search_fields = ("body",)
    raw_id_fields = ("entry", "author")


@admin.register(CarSuggestion)
class CarSuggestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "year_from", "year_to", "user", "created_at", "handled")
    list_filter = ("handled",)
    actions = ["add_to_catalogue"]

    @admin.action(description="Add to catalogue (creates make/model) and mark handled")
    def add_to_catalogue(self, request, qs):
        created = 0
        for s in qs.filter(handled=False):
            make = Make.objects.filter(name__iexact=s.make.strip()).first()
            if not make:
                make = Make.objects.create(name=s.make.strip(), slug=_unique_slug(s.make))
            _car, was_created = CarModel.objects.get_or_create(
                make=make, name=s.model.strip(), generation=s.generation.strip(),
                defaults={"year_from": s.year_from, "year_to": s.year_to},
            )
            created += was_created
            s.handled = True
            s.save(update_fields=["handled"])
        self.message_user(request, f"{created} car model(s) added.")


def _unique_slug(name):
    base = slugify(name) or "make"
    slug, i = base, 2
    while Make.objects.filter(slug=slug).exists():
        slug, i = f"{base}-{i}", i + 1
    return slug


admin.site.register(Vote)
admin.site.register(Bookmark)
