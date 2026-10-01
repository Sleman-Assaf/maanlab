from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path

from core.media import serve_media
from core.sitemaps import ProjectSitemap, StaticViewSitemap
from core.views import robots_txt

sitemaps = {"static": StaticViewSitemap, "projects": ProjectSitemap}

# Language-neutral URLs
urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

# Localised URLs: /en/... and /ar/...
urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    path("projects/", include("projects.urls")),
    path("contact/", include("contact.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    # Range-aware so videos play in Safari and can seek (production: web server / CDN serves /media/).
    urlpatterns += [re_path(r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"), serve_media)]

handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
