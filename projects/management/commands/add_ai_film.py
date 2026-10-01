"""
Add (or update) the AI airline film project, "What Does Royal Mean?".

Media lives in content/portfolio/royal-film/, already encoded for the web:
  loop.mp4 / loop-mobile.mp4   10 s silent loop: 1080p (~2.8 MB) / 960px for phones (~0.9 MB)
                               — hero card, project card, reel, project cover
  film.mp4 / film-mobile.mp4   full 50 s film with sound: 1080p (~27 MB) / 720p for phones (~11 MB)
                               — project page player, loads on play only
  cover.jpg poster; g1..g3.jpg gallery stills

    python manage.py add_ai_film
    python manage.py add_ai_film --media     # replace the files too
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Category, Project, ProjectMedia

FOLDER = Path(settings.BASE_DIR) / "content" / "portfolio" / "royal-film"
SLUG = "what-does-royal-mean"

FIELDS = {
    "category": Category.AI_VIDEO,
    "year": 2026,
    "featured": True,
    "display_order": 4,
    "is_published": True,
    "cover_fit": "fill",
    "title": "What Does Royal Mean? — AI Airline Film",
    "title_ar": "ما معنى أن تكون ملكيًا؟ — فيلم طيران بالذكاء الاصطناعي",
    "short_description": (
        "A 50-second cinematic airline film made with AI — the crew, the journey above the clouds, "
        "and Jordan from Amman's Citadel to Petra."
    ),
    "short_description_ar": (
        "فيلم طيران سينمائي مدته 50 ثانية أُنتج بالذكاء الاصطناعي — طاقم الضيافة، والرحلة فوق الغيوم، "
        "والأردن من جبل القلعة في عمّان إلى البترا."
    ),
    "description": (
        "A brand film built around one question: what does “royal” feel like? The answer runs from the "
        "details of the crew uniform and the warmth of the cabin to a sunset above the clouds and the "
        "places that make Jordan unforgettable.\n\n"
        "Every shot was created with AI — from concept and storyboard to image and video generation — "
        "then edited, colour-graded and finished with sound in-house, ending on the “Fly Royal” signature.\n\n"
        "Delivered as a 16:9 1080p master, with short loops cut for web and social."
    ),
    "description_ar": (
        "فيلم يدور حول سؤال واحد: كيف يبدو الإحساس بأن تكون «ملكيًا»؟ وتأتي الإجابة من تفاصيل زيّ الطاقم ودفء "
        "المقصورة، إلى غروب الشمس فوق الغيوم، والأماكن التي تجعل الأردن تجربة لا تُنسى.\n\n"
        "أُنتجت جميع اللقطات بالذكاء الاصطناعي — من الفكرة والقصة المصوّرة إلى توليد الصور والفيديو — ثم جرى "
        "المونتاج وتصحيح الألوان وإضافة الصوت داخليًا، وصولًا إلى الخاتمة «Fly Royal».\n\n"
        "سُلّم الفيلم بنسخة رئيسية بدقة 1080p ونسبة 16:9، مع مقاطع قصيرة مُعدّة للويب ومنصات التواصل."
    ),
    "deliverables": (
        "Concept & script\nStoryboard\nAI image & video generation\nEdit, colour grade & sound\n"
        "16:9 1080p master + web loops"
    ),
    "deliverables_ar": (
        "الفكرة والنص\nالقصة المصوّرة (Storyboard)\nتوليد الصور والفيديو بالذكاء الاصطناعي\n"
        "المونتاج وتصحيح الألوان والصوت\nنسخة رئيسية 1080p بنسبة 16:9 ومقاطع للويب"
    ),
}

GALLERY = [
    ("g1", "full", "Take-off at golden hour", "الإقلاع في ساعة الغروب الذهبية"),
    ("g2", "half", "Petra, at the end of the Siq", "البترا، عند نهاية السيق"),
    ("g3", "half", "Through the terminal", "عبر صالة المطار"),
]


class Command(BaseCommand):
    help = "Add or update the AI airline film project (What Does Royal Mean?)."

    def add_arguments(self, parser):
        parser.add_argument("--media", action="store_true", help="Replace the video, poster and gallery files.")

    @transaction.atomic
    def handle(self, *args, **options):
        project, created = Project.objects.update_or_create(slug=SLUG, defaults=FIELDS)
        if created or options["media"] or not project.cover_video or not project.cover_video_mobile:
            self._attach_media(project)
        self.stdout.write(f"  {'+' if created else '~'} {project.title}")
        self.stdout.write(self.style.SUCCESS("AI film project ready."))

    def _attach_media(self, project):
        for field, name, target in (
            ("cover_image", "cover.jpg", f"{SLUG}.jpg"),
            ("cover_video", "loop.mp4", f"{SLUG}-loop.mp4"),
            ("cover_video_mobile", "loop-mobile.mp4", f"{SLUG}-loop-mobile.mp4"),
            ("film", "film.mp4", f"{SLUG}-film.mp4"),
            ("film_mobile", "film-mobile.mp4", f"{SLUG}-film-mobile.mp4"),
        ):
            with open(FOLDER / name, "rb") as fh:
                getattr(project, field).save(target, File(fh), save=False)
        project.save()

        project.gallery.all().delete()
        for order, (key, layout, caption, caption_ar) in enumerate(GALLERY):
            item = ProjectMedia(project=project, layout=layout, order=order, caption=caption, caption_ar=caption_ar)
            with open(FOLDER / f"{key}.jpg", "rb") as fh:
                item.image.save(f"{SLUG}-{key}.jpg", File(fh), save=False)
            item.save()
