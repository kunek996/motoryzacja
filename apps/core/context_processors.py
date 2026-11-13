from django.conf import settings
from django.urls import translate_url


def site(request):
    path = request.get_full_path()
    alternates = [(code, translate_url(path, code)) for code, _name in settings.LANGUAGES]
    return {
        "SITE_NAME": "TuneHub",
        "SITE_URL": settings.SITE_URL.rstrip("/"),
        "PRICE_LABEL": "$5",
        "LANGUAGE_ALTERNATES": alternates,
        "ADMIN_PATH": "/" + settings.ADMIN_URL,
        "DEBUG_BANNER": settings.DEBUG,
    }
