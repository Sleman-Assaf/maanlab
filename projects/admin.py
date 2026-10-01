from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Project, ProjectMedia


class ProjectAdminForm(forms.ModelForm):
    also_in = forms.MultipleChoiceField(
        label=_("also show under"),
        choices=Category.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Extra categories whose filter should also list this project (optional)."),
    )

    class Meta:
        model = Project
        fields = "__all__"


class ProjectMediaInline(admin.StackedInline):
    model = ProjectMedia
    extra = 0
    fields = (("image", "video"), ("caption", "caption_ar"), ("layout", "order"), "preview")
    readonly_fields = ("preview",)
    ordering = ("order",)

    @admin.display(description=_("preview"))
    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:120px;border-radius:6px">', obj.image.url)
        if obj and obj.video:
            return format_html('<video src="{}" style="max-height:120px" muted controls></video>', obj.video.url)
        return "—"


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = (
        "thumb",
        "title",
        "category",
        "client",
        "year",
        "media_type",
        "featured",
        "is_published",
        "display_order",
    )
    list_display_links = ("thumb", "title")
    list_editable = ("featured", "is_published", "display_order")
    list_filter = ("category", "is_published", "featured", "year")
    search_fields = ("title", "title_ar", "client", "client_ar", "short_description", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("display_order", "-year")
    inlines = [ProjectMediaInline]
    actions = ("publish", "unpublish", "mark_featured", "unmark_featured")
    readonly_fields = ("cover_preview", "created_at", "updated_at")
    save_on_top = True

    fieldsets = (
        (_("English"), {"fields": ("title", "short_description", "description", "client", "deliverables")}),
        (
            _("Arabic — العربية"),
            {
                "fields": ("title_ar", "short_description_ar", "description_ar", "client_ar", "deliverables_ar"),
                "description": _("Leave a field empty to fall back to the English text on /ar/ pages."),
            },
        ),
        (_("Classification"), {"fields": ("slug", "category", "also_in", "year")}),
        (
            _("Media"),
            {
                "fields": (
                    "cover_image",
                    ("cover_video", "cover_video_mobile"),
                    ("film", "film_mobile"),
                    "thumbnail",
                    "cover_fit",
                    "cover_preview",
                ),
                "description": _(
                    "Add a cover image OR a cover video (or both — the image then becomes the video poster). "
                    "Responsive WebP/AVIF versions are generated automatically."
                ),
            },
        ),
        (_("Links"), {"fields": ("live_url", "repo_url")}),
        (_("Publishing"), {"fields": ("is_published", "featured", "display_order")}),
        (
            _("SEO"),
            {
                "classes": ("collapse",),
                "fields": ("seo_title", "seo_title_ar", "seo_description", "seo_description_ar"),
            },
        ),
        (_("Timestamps"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="")
    def thumb(self, obj):
        url = obj.poster_url
        if url:
            return format_html(
                '<img src="{}" alt="" style="width:72px;height:48px;object-fit:cover;border-radius:4px">', url
            )
        return "🎞" if obj.has_video else "—"

    @admin.display(description=_("media"))
    def media_type(self, obj):
        if obj.cover_video and obj.cover_image:
            return _("Video + poster")
        return _("Video") if obj.cover_video else _("Image")

    @admin.display(description=_("current cover"))
    def cover_preview(self, obj):
        if obj.cover_video:
            return format_html(
                '<video src="{}" poster="{}" style="max-width:420px;border-radius:8px" muted controls></video>',
                obj.cover_video.url,
                obj.poster_url,
            )
        if obj.cover_image:
            return format_html('<img src="{}" style="max-width:420px;border-radius:8px">', obj.cover_image.url)
        return "—"

    @admin.action(description=_("Publish selected projects"))
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description=_("Unpublish selected projects"))
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)

    @admin.action(description=_("Mark as featured"))
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)

    @admin.action(description=_("Remove featured flag"))
    def unmark_featured(self, request, queryset):
        queryset.update(featured=False)
