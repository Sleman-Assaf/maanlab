import tempfile
from pathlib import Path

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from core.media import serve_media
from projects.models import Category, Project


class HomePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Project.objects.create(
            title="Film One",
            title_ar="فيلم واحد",
            slug="film-one",
            category=Category.AI_VIDEO,
            year=2026,
            short_description="A film.",
            is_published=True,
            featured=True,
        )

    def test_root_redirects_to_language_prefix(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/en/"))

    def test_english_homepage(self):
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="en" dir="ltr"', html=False)
        for section in ('id="top"', 'id="services"', 'id="projects"', 'id="about"', 'id="contact"', 'id="site-footer"'):
            self.assertContains(response, section)
        self.assertContains(response, "Digital ideas.")

    def test_arabic_homepage_is_rtl_and_translated(self):
        response = self.client.get("/ar/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="ar" dir="rtl"', html=False)
        self.assertContains(response, "أفكار رقمية.")
        self.assertContains(response, "فيلم واحد")  # Arabic project title
        self.assertContains(response, "Readex+Pro")

    def test_hreflang_and_canonical(self):
        response = self.client.get("/ar/")
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'hreflang="en"')
        self.assertContains(response, 'hreflang="ar"')
        self.assertContains(response, 'hreflang="x-default"')

    def test_language_switch_preserves_page(self):
        response = self.client.get("/en/projects/film-one/")
        self.assertContains(response, 'href="/ar/projects/film-one/"')

    def test_robots_and_sitemap(self):
        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap:", robots.content.decode())
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        body = sitemap.content.decode()
        self.assertIn("/en/projects/film-one/", body)
        self.assertIn("/ar/projects/film-one/", body)
        self.assertIn('hreflang="ar"', body)

    def test_404_page(self):
        response = self.client.get("/en/nothing-here/")
        self.assertEqual(response.status_code, 404)

    def test_reverse_is_language_aware(self):
        with translation.override("ar"):
            self.assertEqual(reverse("core:home"), "/ar/")


class MediaRangeTests(TestCase):
    """Development media view answers Range requests (needed for video in Safari)."""

    def test_range_requests(self):
        with tempfile.TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            Path(root, "clip.mp4").write_bytes(bytes(range(100)))
            get = lambda value: serve_media(RequestFactory().get("/media/clip.mp4", HTTP_RANGE=value), "clip.mp4")

            part = get("bytes=10-19")
            self.assertEqual(part.status_code, 206)
            self.assertEqual(part["Content-Range"], "bytes 10-19/100")
            self.assertEqual(part.content, bytes(range(10, 20)))
            self.assertEqual(get("bytes=-5").content, bytes(range(95, 100)))
            self.assertEqual(get("bytes=200-").status_code, 416)
