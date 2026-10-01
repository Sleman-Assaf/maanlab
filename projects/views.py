from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Project


def _with_brand(title: str) -> str:
    return title if "MAAN LAB" in title else f"{title} — MAAN LAB"


def project_index(request):
    """There is no separate listing page — projects live on the homepage."""
    return redirect(reverse("core:home") + "#projects")


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.published().prefetch_related("gallery"), slug=slug)

    published = list(Project.objects.published().only("pk", "slug", "title", "title_ar", "category"))
    index = next((i for i, p in enumerate(published) if p.pk == project.pk), 0)
    next_project = published[(index + 1) % len(published)] if len(published) > 1 else None

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "gallery": project.gallery.all(),
            "next_project": next_project,
            "page_title": _with_brand(project.seo_title_localized),
            "page_description": project.seo_description_localized,
            "og_image": project.poster_url,
            "og_type": "article",
        },
    )
