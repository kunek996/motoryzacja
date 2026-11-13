from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Minimal inline icon set (stroke icons, 24x24) – no external icon font, CSP friendly.
_ICONS = {
    "thumb": '<path d="M7 10v11H4V10h3zm0 0 4-7a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.3 7.5a2 2 0 0 1-2 1.7H7"/>',
    "comment": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4z"/>',
    "download": '<path d="M12 3v12m0 0-4-4m4 4 4-4M4 17v3h16v-3"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16v4zM14 6l4 4"/>',
    "trash": '<path d="M4 7h16M10 11v6m4-6v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "flag": '<path d="M5 21V4m0 0h11l-2 4 2 4H5"/>',
    "gauge": '<path d="M4 18a8 8 0 1 1 16 0M12 18l4-6"/><circle cx="12" cy="18" r="1.4"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M4.9 4.9l2.1 2.1m10 10 2.1 2.1M4.9 19.1 7 17m10-10 2.1-2.1"/>',
    "turbo": '<circle cx="12" cy="12" r="8"/><path d="M12 4c2 3 2 5 0 8s-2 5 0 8M4 12c3-2 5-2 8 0s5 2 8 0"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0 5 5L21 13l-8 8-3-3 8-8-1.3-1.3a4 4 0 0 1-5-5L13 2z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "file": '<path d="M14 3H6v18h12V7zM14 3v4h4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
}


@register.simple_tag
def icon(name, css="icon"):
    body = _ICONS.get(name, "")
    return format_html(
        '<svg class="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>',
        css,
        mark_safe(body),  # noqa: S308 – constant markup from _ICONS
    )


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Current query string with some keys replaced, e.g. {% url_replace page=3 %}."""
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return "?" + query.urlencode() if query else "?"


@register.filter
def initial(value):
    text = str(value or "?")
    return text[:1].upper()


_JSON_ESCAPES = {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}


@register.filter
def ld_json(data):
    """Render a dict as a JSON-LD <script> block (HTML-safe escaping, not executed by browsers)."""
    import json

    if not data:
        return ""
    payload = json.dumps(data, ensure_ascii=False, default=str).translate(_JSON_ESCAPES)
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')  # noqa: S308 – escaped above


CATEGORY_ICONS ={"mod": "wrench", "ecu": "gauge", "tcu": "gear", "turbo": "turbo", "other": "file"}


@register.simple_tag
def category_icon(category):
    return icon(CATEGORY_ICONS.get(category, "file"))
