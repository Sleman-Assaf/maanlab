from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import HeroMedia

admin.site.site_header = "MAAN LAB"
admin.site.site_title = "MAAN LAB Admin"
admin.site.index_title = _("Website content")


@admin.register(HeroMedia)
class HeroMediaAdmin(admin.ModelAdmin):
    list_display = ("label", "preview", "is_active", "updated_at")
    list_editable = ("is_active",)
    readonly_fields = ("preview",)
    fieldsets = (
        (None, {"fields": ("label", "is_active")}),
        (
            _("Object"),
            {
                "fields": ("image", "video", "video_poster", "preview"),
                "description": _(
                    "One simple premium technology object, presented like a product. "
                    "Use a transparent PNG/WebP cut-out — or a short muted loop with a poster."
                ),
            },
        ),
        (_("Accessibility"), {"fields": ("alt_text", "alt_text_ar")}),
    )

    @admin.display(description=_("preview"))
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:160px;background:#111;padding:8px;border-radius:8px">', obj.image.url
            )
        if obj.video_poster:
            return format_html('<img src="{}" style="max-height:160px;border-radius:8px">', obj.video_poster.url)
        return "—"
