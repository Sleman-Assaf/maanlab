from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.i18n import TranslatableMixin
from core.imaging import ResponsiveImagesMixin, upload_to
from core.validators import IMAGE_VALIDATORS, VIDEO_VALIDATORS


class Category(models.TextChoices):
    AI_VIDEO = "ai_video", _("AI Video")
    AI_AUTOMATION = "ai_automation", _("AI & Automation")
    WEB_DEVELOPMENT = "web_development", _("Web Development")
    DIGITAL_TRANSFORMATION = "digital_transformation", _("Digital Transformation")


class ProjectQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class Project(TranslatableMixin, ResponsiveImagesMixin):
    RESPONSIVE_IMAGE_FIELDS = ("cover_image", "thumbnail")

    # --- English -----------------------------------------------------------
    title = models.CharField(_("title (English)"), max_length=200)
    short_description = models.CharField(
        _("short description (English)"),
        max_length=300,
        help_text=_("One or two sentences shown on project cards."),
    )
    description = models.TextField(
        _("description (English)"),
        blank=True,
        help_text=_("Full case study text. Separate paragraphs with an empty line."),
    )
    client = models.CharField(_("client (English)"), max_length=150, blank=True)
    deliverables = models.TextField(
        _("deliverables (English)"), blank=True, help_text=_("One item per line.")
    )

    # --- Arabic ------------------------------------------------------------
    title_ar = models.CharField(_("title (Arabic)"), max_length=200, blank=True)
    short_description_ar = models.CharField(_("short description (Arabic)"), max_length=300, blank=True)
    description_ar = models.TextField(_("description (Arabic)"), blank=True)
    client_ar = models.CharField(_("client (Arabic)"), max_length=150, blank=True)
    deliverables_ar = models.TextField(_("deliverables (Arabic)"), blank=True)

    # --- Classification -----------------------------------------------------
    slug = models.SlugField(
        _("slug"), max_length=120, unique=True, help_text=_("Used in the URL: /en/projects/<slug>/")
    )
    category = models.CharField(_("category"), max_length=32, choices=Category.choices, db_index=True)
    also_in = models.JSONField(
        _("also show under"),
        default=list,
        blank=True,
        help_text=_("Extra categories whose filter should also list this project (optional)."),
    )
    year = models.PositiveSmallIntegerField(
        _("year"), validators=[MinValueValidator(1990), MaxValueValidator(2100)]
    )

    # --- Media --------------------------------------------------------------
    cover_image = models.ImageField(
        _("cover image"),
        upload_to=upload_to("projects/covers"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text=_("Main visual (16:10 recommended, 2400px wide). Also used as the video poster."),
    )
    cover_video = models.FileField(
        _("cover video"),
        upload_to=upload_to("projects/videos"),
        blank=True,
        validators=VIDEO_VALIDATORS,
        help_text=_("Optional MP4/WebM. Plays muted as a preview on hover and on the project page."),
    )
    cover_video_mobile = models.FileField(
        _("cover video — phone version"),
        upload_to=upload_to("projects/videos"),
        blank=True,
        validators=VIDEO_VALIDATORS,
        help_text=_("Optional smaller copy of the cover video (about 960px wide) used on phones to save data."),
    )
    film = models.FileField(
        _("full film"),
        upload_to=upload_to("projects/films"),
        blank=True,
        validators=VIDEO_VALIDATORS,
        help_text=_(
            "Optional complete video with sound, shown with a player on the project page. "
            "It loads only when the visitor presses play. Keep the cover video a short, light loop."
        ),
    )
    film_mobile = models.FileField(
        _("full film — phone version"),
        upload_to=upload_to("projects/films"),
        blank=True,
        validators=VIDEO_VALIDATORS,
        help_text=_("Optional smaller copy of the full film (about 1280px wide) played on phones."),
    )
    thumbnail = models.ImageField(
        _("card thumbnail"),
        upload_to=upload_to("projects/thumbnails"),
        blank=True,
        validators=IMAGE_VALIDATORS,
        help_text=_("Optional image for the homepage card. Falls back to the cover image."),
    )

    # --- Links --------------------------------------------------------------
    cover_fit = models.CharField(
        _("cover display"),
        max_length=10,
        choices=[
            ("fill", _("Fill the frame — photos and videos")),
            ("screen", _("Show the whole image — screenshots and interfaces")),
        ],
        default="fill",
        help_text=_("“Show the whole image” keeps screenshots uncropped on a dark frame. Applies to the cover and gallery images."),
    )

    live_url = models.URLField(
        _("live site URL"), blank=True, help_text=_("Public link to the running website or app (optional).")
    )
    repo_url = models.URLField(
        _("source code URL"), blank=True, help_text=_("Link to the code repository, e.g. GitHub (optional).")
    )

    # --- Publishing ---------------------------------------------------------
    featured = models.BooleanField(_("featured"), default=False, help_text=_("Shown as a wide card."))
    display_order = models.PositiveIntegerField(_("display order"), default=0, db_index=True)
    is_published = models.BooleanField(_("published"), default=False)

    # --- SEO ----------------------------------------------------------------
    seo_title = models.CharField(_("SEO title (English)"), max_length=70, blank=True)
    seo_title_ar = models.CharField(_("SEO title (Arabic)"), max_length=70, blank=True)
    seo_description = models.CharField(_("SEO description (English)"), max_length=170, blank=True)
    seo_description_ar = models.CharField(_("SEO description (Arabic)"), max_length=170, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["display_order", "-year", "-created_at"]
        verbose_name = _("project")
        verbose_name_plural = _("projects")
        indexes = [models.Index(fields=["is_published", "category"])]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.cover_image and not self.cover_video:
            raise ValidationError(
                {"cover_image": _("Add a cover image or a cover video — at least one is required.")}
            )

    @property
    def categories(self) -> list[str]:
        """Main category first, then any extra ones — used by the project filter."""
        valid = set(Category.values)
        extra = [c for c in (self.also_in or []) if c in valid and c != self.category]
        return [self.category, *dict.fromkeys(extra)]

    @property
    def categories_attr(self) -> str:
        return " ".join(self.categories)

    def get_absolute_url(self):
        return reverse("projects:detail", kwargs={"slug": self.slug})

    # --- Presentation helpers ------------------------------------------------
    @property
    def has_video(self) -> bool:
        return bool(self.cover_video)

    @property
    def card_image_field(self) -> str | None:
        if self.thumbnail:
            return "thumbnail"
        if self.cover_image:
            return "cover_image"
        return None

    @property
    def poster_url(self) -> str:
        field = self.card_image_field
        return getattr(self, field).url if field else ""

    def localized_deliverables(self) -> list[str]:
        raw = self.localized("deliverables") or ""
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def localized_paragraphs(self) -> list[str]:
        raw = (self.localized("description") or "").replace("\r\n", "\n")
        return [p.strip() for p in raw.split("\n\n") if p.strip()]

    @property
    def seo_title_localized(self) -> str:
        return self.localized("seo_title") or self.localized("title")

    @property
    def seo_description_localized(self) -> str:
        return self.localized("seo_description") or self.localized("short_description")


class ProjectMedia(TranslatableMixin, ResponsiveImagesMixin):
    """Gallery item shown on the project detail page."""

    RESPONSIVE_IMAGE_FIELDS = ("image",)

    class Layout(models.TextChoices):
        FULL = "full", _("Full width")
        HALF = "half", _("Half width")

    project = models.ForeignKey(Project, related_name="gallery", on_delete=models.CASCADE)
    image = models.ImageField(
        _("image"), upload_to=upload_to("projects/gallery"), blank=True, validators=IMAGE_VALIDATORS
    )
    video = models.FileField(
        _("video"), upload_to=upload_to("projects/gallery"), blank=True, validators=VIDEO_VALIDATORS
    )
    caption = models.CharField(_("caption (English)"), max_length=200, blank=True)
    caption_ar = models.CharField(_("caption (Arabic)"), max_length=200, blank=True)
    layout = models.CharField(_("layout"), max_length=8, choices=Layout.choices, default=Layout.FULL)
    order = models.PositiveIntegerField(_("order"), default=0)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = _("gallery item")
        verbose_name_plural = _("gallery")

    def __str__(self):
        return self.caption or f"{self.project} — #{self.order}"

    def clean(self):
        if not self.image and not self.video:
            raise ValidationError(_("Add an image or a video."))
