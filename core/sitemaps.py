from urllib.parse import urlparse

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.models import Project

_site = urlparse(settings.SITE_URL)


class _BaseSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = True
    protocol = _site.scheme or "https"

    def get_domain(self, site=None):
        return _site.netloc or super().get_domain(site)


class StaticViewSitemap(_BaseSitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["core:home"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(_BaseSitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return Project.objects.published().order_by("display_order", "pk")

    def lastmod(self, obj):
        return obj.updated_at
