from django.conf import settings
from django.urls import translate_url
from django.utils import timezone

from .i18n import current_language, is_rtl


def _alternate(path: str, current: str, target: str) -> str:
    url = translate_url(path, target)
    prefix = f"/{current}/"
    if url == path and path.startswith(prefix) and current != target:
        url = f"/{target}/" + path[len(prefix):]
    return url


def site(request):
    language = current_language()
    path = request.path
    alternates = {code: _alternate(path, language, code) for code, _name in settings.LANGUAGES}
    return {
        "SITE_NAME": "MAAN LAB",
        "SITE_URL": settings.SITE_URL,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "SOCIAL_LINKS": settings.SOCIAL_LINKS,
        "CURRENT_YEAR": timezone.localdate().year,
        "LANG": language,
        "IS_RTL": is_rtl(language),
        "ALT_URLS": alternates,
        "CANONICAL_URL": f"{settings.SITE_URL}{path}",
        "OG_LOCALE": "ar_JO" if language == "ar" else "en_US",
    }
