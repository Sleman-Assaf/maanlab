from django.db import models
from django.utils.translation import gettext_lazy as _


class ServiceChoice(models.TextChoices):
    AI_AUTOMATION = "ai_automation", _("AI & Automation")
    WEB_DEVELOPMENT = "web_development", _("Web Development")
    AI_VIDEO = "ai_video", _("AI Video Generation")
    DIGITAL_TRANSFORMATION = "digital_transformation", _("Digital Transformation")
    OTHER = "other", _("Other")


class LanguageChoice(models.TextChoices):
    EN = "en", "English"
    AR = "ar", "العربية"


class ContactMessage(models.Model):
    name = models.CharField(_("name"), max_length=120)
    email = models.EmailField(_("email"))
    phone = models.CharField(_("phone"), max_length=32, blank=True)
    company = models.CharField(_("company / business"), max_length=160, blank=True)
    service = models.CharField(_("service"), max_length=32, choices=ServiceChoice.choices)
    preferred_language = models.CharField(
        _("preferred language"), max_length=2, choices=LanguageChoice.choices, default=LanguageChoice.EN
    )
    message = models.TextField(_("message"))
    submitted_from = models.CharField(_("site language"), max_length=5, blank=True, editable=False)
    created_at = models.DateTimeField(_("received"), auto_now_add=True, db_index=True)
    is_read = models.BooleanField(_("read"), default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("contact message")
        verbose_name_plural = _("contact messages")

    def __str__(self):
        return f"{self.name} — {self.get_service_display()}"
