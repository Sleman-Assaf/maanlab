"""Helpers for bilingual (English/Arabic) model content."""
from django.conf import settings
from django.utils.translation import get_language


def current_language() -> str:
    return (get_language() or settings.LANGUAGE_CODE).split("-")[0]


def is_rtl(language: str | None = None) -> bool:
    return (language or current_language()) in settings.RTL_LANGUAGES


class _Localized:
    """Template-friendly accessor: `{{ project.t.title }}`."""

    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return self._obj.localized(name)


class TranslatableMixin:
    """
    Content fields are stored as `<field>` (English) and `<field>_ar` (Arabic).
    `localized(field)` returns the Arabic value when the active language is
    Arabic and a translation exists, otherwise the English value.
    """

    def localized(self, field: str):
        if current_language() == "ar":
            value = getattr(self, f"{field}_ar", "")
            if value:
                return value
        return getattr(self, field, "")

    @property
    def t(self):
        return _Localized(self)
