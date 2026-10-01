import shutil
import tempfile
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import translation
from PIL import Image

from .models import Category, Project

TEMP_MEDIA = tempfile.mkdtemp()


def image_file(name="cover.jpg", size=(1000, 600)):
    buffer = BytesIO()
    Image.new("RGB", size, (200, 100, 50)).save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProjectModelTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def make(self, **kwargs):
        data = {
            "title": "Automation",
            "slug": "automation",
            "category": Category.AI_AUTOMATION,
            "year": 2025,
            "short_description": "Short",
            "is_published": True,
        }
        data.update(kwargs)
        return Project(**data)

    def test_requires_image_or_video(self):
        project = self.make()
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_image_only_is_valid(self):
        project = self.make(cover_image=image_file())
        project.full_clean()

    def test_video_only_is_valid(self):
        video = SimpleUploadedFile("clip.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")
        project = self.make(cover_video=video)
        project.full_clean()

    def test_rejects_unsafe_video_extension(self):
        video = SimpleUploadedFile("clip.exe", b"x", content_type="application/octet-stream")
        project = self.make(cover_video=video)
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_responsive_variants_are_generated(self):
        project = self.make(cover_image=image_file(size=(1000, 600)))
        project.save()
        project.refresh_from_db()
        variants = project.variants_for("cover_image")
        self.assertEqual(variants["width"], 1000)
        self.assertTrue(variants["webp"])
        self.assertEqual([w for w, _ in variants["webp"]], [480, 800, 1000])

    def test_localized_fields_fall_back_to_english(self):
        project = self.make(title_ar="أتمتة", short_description_ar="")
        with translation.override("ar"):
            self.assertEqual(project.t.title, "أتمتة")
            self.assertEqual(project.t.short_description, "Short")
        with translation.override("en"):
            self.assertEqual(project.t.title, "Automation")


class ProjectViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.web = Project.objects.create(
            title="Web", slug="web", category=Category.WEB_DEVELOPMENT, year=2025,
            short_description="Web project", is_published=True, description="Para one.\n\nPara two.",
        )
        cls.film = Project.objects.create(
            title="Film", title_ar="فيلم", slug="film", category=Category.AI_VIDEO, year=2026,
            short_description="Film project", is_published=True,
        )
        cls.draft = Project.objects.create(
            title="Draft", slug="draft", category=Category.AI_VIDEO, year=2026,
            short_description="Hidden", is_published=False,
        )

    def test_all_published_projects_are_server_rendered(self):
        response = self.client.get("/en/")
        self.assertContains(response, 'data-category="web_development"')
        self.assertContains(response, 'data-category="ai_video"')
        self.assertNotContains(response, "Draft")

    def test_category_query_marks_others_hidden_without_js(self):
        response = self.client.get("/en/?category=ai_video")
        html = response.content.decode().replace("\r", "")
        # Both are rendered (SSR); only the non-matching one carries `hidden`.
        self.assertEqual(html.count('class="project-grid__item'), 2)
        self.assertRegex(html, r'data-category="web_development"\s+hidden>')
        self.assertNotRegex(html, r'data-category="ai_video"\s+hidden>')
        self.assertIn('data-filter="ai_video"\n           aria-pressed="true"', html)

    def test_also_in_lists_project_under_extra_category(self):
        self.film.also_in = [Category.WEB_DEVELOPMENT.value]
        self.film.save()
        response = self.client.get("/en/?category=web_development")
        html = response.content.decode().replace("\r", "")
        self.assertIn('data-category="ai_video web_development"\n', html)
        self.assertNotRegex(html, r'data-category="ai_video web_development"\s+hidden>')
        web_filter = next(f for f in response.context["filters"] if f["key"] == "web_development")
        self.assertEqual(web_filter["count"], 2)

    def test_invalid_category_falls_back_to_all(self):
        response = self.client.get("/en/?category=<script>")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_category"], "all")

    def test_detail_page_en_and_ar(self):
        en = self.client.get("/en/projects/film/")
        self.assertEqual(en.status_code, 200)
        self.assertContains(en, "Film")
        ar = self.client.get("/ar/projects/film/")
        self.assertEqual(ar.status_code, 200)
        self.assertContains(ar, "فيلم")
        self.assertContains(ar, 'dir="rtl"')

    def test_detail_paragraphs(self):
        response = self.client.get("/en/projects/web/")
        self.assertContains(response, "Para one.")
        self.assertContains(response, "Para two.")

    def test_unpublished_project_is_404(self):
        self.assertEqual(self.client.get("/en/projects/draft/").status_code, 404)

    def test_projects_index_redirects_to_homepage_section(self):
        response = self.client.get("/en/projects/")
        self.assertRedirects(response, "/en/#projects", fetch_redirect_response=False)
