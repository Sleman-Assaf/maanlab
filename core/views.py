from collections import Counter

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from projects.models import Category, Project

from .content import ABOUT_KEYWORDS, SERVICES
from .i18n import current_language
from .models import HeroMedia


def build_home_context(request, contact_form=None) -> dict:
    from contact.forms import ContactForm  # local import avoids an app-loading cycle

    projects = list(Project.objects.published())
    valid = {c.value for c in Category}
    active_category = request.GET.get("category", "all")
    if active_category not in valid:
        active_category = "all"

    counts = Counter(c for p in projects for c in p.categories)
    filters = [{"key": "all", "label": _("All"), "count": len(projects)}] + [
        {"key": c.value, "label": c.label, "count": counts.get(c.value, 0)} for c in Category
    ]

    films = [p for p in projects if p.category == Category.AI_VIDEO]
    featured_film = next((p for p in films if p.featured), films[0] if films else None)

    return {
        "hero_media": HeroMedia.get_active(),
        "services": SERVICES,
        "projects": projects,
        "filters": filters,
        "active_category": active_category,
        "featured_film": featured_film,
        "reel_project": next((p for p in films if p.cover_video), None),
        "about_keywords": ABOUT_KEYWORDS,
        "stats": {"projects": len(projects), "disciplines": len(SERVICES), "languages": len(settings.LANGUAGES)},
        "contact_form": contact_form or ContactForm(language=current_language()),
        "page_title": _("MAAN LAB — Creative Technology Studio from Ma'an, Jordan"),
        "page_description": _(
            "AI & automation, web development, AI video production and digital transformation — "
            "built by MAAN LAB in Ma'an, Jordan."
        ),
        "is_home": True,
    }


def render_home(request, contact_form=None, status=200):
    return render(request, "home.html", build_home_context(request, contact_form), status=status)


@require_GET
def home(request):
    return render_home(request)


@require_GET
@cache_control(max_age=86400, public=True)
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Allow: /",
        "",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def page_not_found(request, exception=None):
    return render(request, "404.html", {"page_title": _("Page not found — MAAN LAB")}, status=404)


def server_error(request):
    # Standalone template: must render even if the database or context processors fail.
    return HttpResponse(loader.get_template("500.html").render({}), status=500)
