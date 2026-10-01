from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .i18n import TranslatableMixin
from .imaging import ResponsiveImagesMixin, upload_to
from .validators import IMAGE_VALIDATORS, VIDEO_VALIDATORS


class HeroMedia(TranslatableMixin, ResponsiveImagesMixin):
    """
    The hero "object" — one premium technology object presented like a product.

    Upload either a transparent PNG/WebP cut-out (recommended, ~1600px) or a
    short muted video loop with a poster. The most recently updated active
    entry is used. With no entry, the site falls back to the bundled
    placeholder object.
    """

    RESPONSIVE_IMAGE_FIELDS = ("image", "video_poster")

    label = models.CharField(_("internal label"), max_length=120, default="Hero object")
    image = models.ImageField(
        _("object image"),
        upload_to=upload_to("hero"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text=_("Transparent PNG or WebP cut-out of the object. Around 1600×1600px works best."),
    )
    video = models.FileField(
        _("object video"),
        upload_to=upload_to("hero/video"),
        blank=True,
        validators=VIDEO_VALIDATORS,
        help_text=_("Optional short MP4/WebM loop (muted). Shown instead of the image."),
    )
    video_poster = models.ImageField(
        _("video poster"),
        upload_to=upload_to("hero/poster"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text=_("First frame of the video. Loaded before the video."),
    )
    alt_text = models.CharField(_("alt text (English)"), max_length=200, blank=True)
    alt_text_ar = models.CharField(_("alt text (Arabic)"), max_length=200, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("hero media")
        verbose_name_plural = _("hero media")
        ordering = ["-updated_at"]

    def __str__(self):
        return self.label

    def clean(self):
        if not self.image and not self.video:
            raise ValidationError(_("Add an object image or a video."))

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()
