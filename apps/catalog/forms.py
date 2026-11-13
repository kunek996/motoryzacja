import os

from django import forms
from django.conf import settings
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import CarModel, CarSuggestion, Comment, Entry, EntryParameter, Make, Report

# Content signatures we never accept, whatever the extension says.
FORBIDDEN_SIGNATURES = (
    b"MZ",  # Windows PE executables / DLLs
    b"\x7fELF",  # Linux executables
    b"#!",  # scripts
    b"\xca\xfe\xba\xbe",  # Mach-O / Java class
    b"\xcf\xfa\xed\xfe",  # Mach-O 64
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def validate_upload(f):
    """Extension allow-list + size limit + content sniffing. Raises ValidationError."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in settings.ATTACHMENT_ALLOWED_EXTENSIONS:
        raise forms.ValidationError(
            _("File type not allowed. Allowed: %(types)s")
            % {"types": ", ".join(sorted(settings.ATTACHMENT_ALLOWED_EXTENSIONS))}
        )
    if f.size > settings.ATTACHMENT_MAX_BYTES:
        raise forms.ValidationError(_("File too large."))
    head = f.read(8)
    f.seek(0)
    if any(head.startswith(sig) for sig in FORBIDDEN_SIGNATURES):
        raise forms.ValidationError(_("This file looks like an executable and cannot be uploaded."))
    if ext in IMAGE_EXTENSIONS:
        from PIL import Image

        try:
            Image.open(f).verify()
        except Exception:  # noqa: BLE001
            raise forms.ValidationError(_("The image file is damaged or not an image."))
        finally:
            f.seek(0)
    return f


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data if d]
        return [single(data, initial)] if data else []


def grouped_car_choices():
    groups = {}
    for m in CarModel.objects.select_related("make"):
        label = " ".join(p for p in (m.name, m.generation) if p)
        if m.years:
            label += f" ({m.years})"
        groups.setdefault(m.make.name, []).append((m.pk, label))
    return [("", "---------")] + list(groups.items())


class EntryForm(forms.ModelForm):
    attachments = MultipleFileField(required=False, label=_("Attachments (maps, logs, photos)"))

    class Meta:
        model = Entry
        fields = [
            "car_model", "category", "title", "language", "model_year", "fuel", "engine", "ecu_type",
            "gearbox", "stage", "turbo", "boost_bar",
            "power_before_hp", "power_after_hp", "torque_before_nm", "torque_after_nm", "body",
        ]
        widgets = {"body": forms.Textarea(attrs={"rows": 10})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["car_model"].choices = grouped_car_choices()
        self.fields["attachments"].help_text = _("Up to %(n)s files, max %(mb)s MB each.") % {
            "n": settings.ATTACHMENT_MAX_PER_ENTRY,
            "mb": settings.ATTACHMENT_MAX_BYTES // (1024 * 1024),
        }

    def clean_attachments(self):
        files = self.cleaned_data.get("attachments") or []
        existing = self.instance.attachments.count() if self.instance.pk else 0
        if existing + len(files) > settings.ATTACHMENT_MAX_PER_ENTRY:
            raise forms.ValidationError(
                _("Too many attachments (max %(n)s per entry).") % {"n": settings.ATTACHMENT_MAX_PER_ENTRY}
            )
        for f in files:
            validate_upload(f)
        return files

    def clean(self):
        data = super().clean()
        for before, after in (("power_before_hp", "power_after_hp"), ("torque_before_nm", "torque_after_nm")):
            b, a = data.get(before), data.get(after)
            if b and a and a > b * 3:
                self.add_error(after, _("This value looks unrealistic. Please double-check."))
        return data


ParameterFormSet = inlineformset_factory(
    Entry,
    EntryParameter,
    fields=("name", "value", "unit"),
    extra=3,
    max_num=30,
    can_delete=True,
    widgets={
        "name": forms.TextInput(attrs={"placeholder": _("e.g. Boost target @ 4000 rpm")}),
        "value": forms.TextInput(attrs={"placeholder": "1.45"}),
        "unit": forms.TextInput(attrs={"placeholder": "bar", "size": 6}),
    },
)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}
        labels = {"body": ""}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason"]
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}


class CarSuggestionForm(forms.ModelForm):
    class Meta:
        model = CarSuggestion
        fields = ["make", "model", "generation", "year_from", "year_to"]

    def clean(self):
        data = super().clean()
        y1, y2 = data.get("year_from"), data.get("year_to")
        if y1 and y2 and y2 < y1:
            self.add_error("year_to", _("The end year must not be earlier than the start year."))
        return data


class EntryFilterForm(forms.Form):
    SORTS = [("new", _("Newest")), ("top", _("Most helpful")), ("discussed", _("Most discussed"))]

    q = forms.CharField(required=False, label=_("Search"), widget=forms.SearchInput(attrs={"placeholder": _("Title, engine, ECU, turbo…")}))
    make = forms.ModelChoiceField(Make.objects.all(), required=False, label=_("Make"), empty_label=_("All makes"))
    car_model = forms.ModelChoiceField(
        CarModel.objects.select_related("make"), required=False, label=_("Model"), empty_label=_("All models")
    )
    category = forms.ChoiceField(required=False, label=_("Category"), choices=[("", _("All categories"))] + list(Entry.Category.choices))
    fuel = forms.ChoiceField(required=False, label=_("Fuel"), choices=[("", _("Any fuel"))] + list(Entry.Fuel.choices))
    stage = forms.ChoiceField(required=False, label=_("Stage"), choices=[("", _("Any stage"))] + list(Entry.Stage.choices))
    language = forms.ChoiceField(required=False, label=_("Language"), choices=[("", _("Any language"))] + list(Entry.Language.choices))
    sort = forms.ChoiceField(required=False, label=_("Sort"), choices=SORTS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        make_id = self.data.get("make")
        if make_id and str(make_id).isdigit():
            self.fields["car_model"].queryset = CarModel.objects.filter(make_id=make_id).select_related("make")
