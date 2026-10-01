from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("status", "name", "email", "phone", "company", "service", "preferred_language", "created_at", "is_read")
    list_display_links = ("name",)
    list_editable = ("is_read",)
    list_filter = ("is_read", "service", "preferred_language", "created_at")
    search_fields = ("name", "email", "company", "phone", "message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ("mark_read", "mark_unread")
    list_per_page = 50
    readonly_fields = (
        "name",
        "email_link",
        "phone",
        "company",
        "service",
        "preferred_language",
        "message",
        "submitted_from",
        "created_at",
    )
    fieldsets = (
        (_("Sender"), {"fields": ("name", "email_link", "phone", "company")}),
        (_("Inquiry"), {"fields": ("service", "preferred_language", "message")}),
        (_("Status"), {"fields": ("is_read", "submitted_from", "created_at")}),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="", ordering="is_read")
    def status(self, obj):
        color = "#9a9187" if obj.is_read else "#dd6b2f"
        label = _("read") if obj.is_read else _("new")
        return format_html(
            '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{}" title="{}"></span>',
            color,
            label,
        )

    @admin.display(description=_("email"))
    def email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.email)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Opening a message marks it as read.
        ContactMessage.objects.filter(pk=object_id, is_read=False).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description=_("Mark selected messages as read"))
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, _("%(count)d message(s) marked as read.") % {"count": updated})

    @admin.action(description=_("Mark selected messages as unread"))
    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, _("%(count)d message(s) marked as unread.") % {"count": updated})
