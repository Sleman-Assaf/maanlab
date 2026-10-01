"""
Add (or update) the real MAAN LAB projects published on GitHub
(https://github.com/Sleman-Assaf): Nabatati, LingoVoice and Maktabati.

Screenshots live in content/portfolio/<slug>/ (cover.jpg + g1..g3.jpg).
Running the command again updates text and links; add --media to replace images.

    python manage.py add_github_projects
    python manage.py add_github_projects --media
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Category, Project, ProjectMedia

CONTENT = Path(settings.BASE_DIR) / "content" / "portfolio"
DEMO_SLUGS = [
    "sandstone-product-film", "monthly-reporting-automated", "bilingual-corporate-platform",
    "from-spreadsheets-to-system", "night-market-campaign", "arabic-ai-call-assistant", "clinic-booking-web-app",
]

PROJECTS = [
    {
        "slug": "nabatati",
        "category": Category.AI_AUTOMATION,
        "also_in": [Category.WEB_DEVELOPMENT],
        "year": 2026,
        "featured": True,
        "order": 1,
        "live_url": "https://sleman-assaf.github.io/Nabatati-new/",
        "repo_url": "https://github.com/Sleman-Assaf/Nabatati-new",
        "title": "Nabatati — AI Plant Health Platform",
        "title_ar": "نباتاتي — منصة ذكية لصحة النباتات",
        "short": "A web platform that diagnoses olive-leaf diseases from a photo, answers plant-care questions with an AI assistant, and connects growers with agricultural engineers.",
        "short_ar": "منصة ويب تشخّص أمراض أوراق الزيتون من صورة، وتجيب عن أسئلة العناية بالنباتات عبر مساعد ذكي، وتربط المزارعين بالمهندسين الزراعيين.",
        "description": (
            "Nabatati helps growers catch plant problems early. A user uploads a photo of an olive leaf, and a trained "
            "deep-learning model classifies it as healthy or identifies the disease, with a confidence score.\n\n"
            "Alongside diagnosis, a Gemini-powered chatbot answers plant-care questions, and growers can request a "
            "consultation with an agricultural engineer and continue the conversation in a real-time chat.\n\n"
            "Built with an Angular front end, a Django REST Framework API with JWT and Google sign-in, a TensorFlow/Keras "
            "image model, and a Node.js and Socket.io service for live chat."
        ),
        "description_ar": (
            "تساعد نباتاتي المزارعين على اكتشاف مشكلات النباتات مبكرًا. يرفع المستخدم صورة لورقة زيتون، فيصنّفها نموذج "
            "تعلّم عميق مدرَّب على أنها سليمة أو يحدد نوع المرض، مع نسبة الثقة في النتيجة.\n\n"
            "وإلى جانب التشخيص، يجيب مساعد ذكي مدعوم بـ Gemini عن أسئلة العناية بالنباتات، ويمكن للمزارعين طلب استشارة "
            "من مهندس زراعي ومتابعة الحديث عبر محادثة فورية.\n\n"
            "بُنيت المنصة بواجهة Angular، وواجهة برمجية Django REST Framework مع تسجيل الدخول عبر JWT وGoogle، ونموذج صور "
            "TensorFlow/Keras، وخدمة Node.js وSocket.io للمحادثة المباشرة."
        ),
        "deliverables": "AI plant-disease diagnosis\nGemini AI chatbot\nExpert consultations & live chat\nAngular front end\nDjango REST API with Google sign-in",
        "deliverables_ar": "تشخيص أمراض النباتات بالذكاء الاصطناعي\nمساعد ذكي مدعوم بـ Gemini\nاستشارات الخبراء والمحادثة المباشرة\nواجهة Angular\nواجهة برمجية Django REST مع تسجيل الدخول عبر Google",
        "gallery": [
            ("g1", "full", "Services: AI diagnosis, smart chatbot and expert consultations", "الخدمات: التشخيص الذكي، والمساعد الذكي، واستشارات الخبراء"),
            ("g2", "half", "Home page on mobile", "الصفحة الرئيسية على الهاتف"),
            ("g3", "half", "Sign-in screen on mobile", "شاشة تسجيل الدخول على الهاتف"),
        ],
    },
    {
        "slug": "lingovoice",
        "category": Category.AI_AUTOMATION,
        "also_in": [Category.WEB_DEVELOPMENT],
        "year": 2026,
        "featured": False,
        "order": 2,
        "live_url": "https://sleman-assaf.github.io/LingoVoice/",
        "repo_url": "https://github.com/Sleman-Assaf/LingoVoice",
        "title": "LingoVoice — AI Speaking Coach",
        "title_ar": "LingoVoice — مدرّب محادثة بالذكاء الاصطناعي",
        "short": "A language-learning web app where learners practise speaking out loud and get instant AI feedback on grammar and pronunciation, plus a spoken reply.",
        "short_ar": "تطبيق ويب لتعلّم اللغات يتدرّب فيه المتعلم على التحدث بصوته، ويحصل فورًا على ملاحظات ذكية حول القواعد والنطق مع رد صوتي.",
        "description": (
            "LingoVoice turns speaking practice into a real conversation. Learners record their voice; the system "
            "transcribes it, corrects grammar and pronunciation, explains the feedback in Arabic, and replies with an "
            "AI-generated voice in the target language.\n\n"
            "Sessions are saved and can be exported as PDF reports, and an admin dashboard manages courses and users.\n\n"
            "Built with Angular and an ASP.NET Core Web API (C#, Entity Framework Core, SQL Server), JWT authentication, "
            "WebSockets for real-time communication, QuestPDF and MailKit, with the Gemini API for speech and conversation."
        ),
        "description_ar": (
            "يحوّل LingoVoice التدريب على التحدث إلى محادثة حقيقية. يسجّل المتعلم صوته، فيحوّله النظام إلى نص، ويصحح "
            "القواعد والنطق، ويشرح الملاحظات باللغة العربية، ثم يرد بصوت مولَّد بالذكاء الاصطناعي باللغة المستهدفة.\n\n"
            "تُحفظ الجلسات ويمكن تصديرها كتقارير PDF، وتتيح لوحة تحكم للمسؤولين إدارة الدورات والمستخدمين.\n\n"
            "بُني التطبيق بواجهة Angular وواجهة برمجية ASP.NET Core Web API (C# وEntity Framework Core وSQL Server)، مع "
            "مصادقة JWT، واتصال فوري عبر WebSockets، وQuestPDF وMailKit، وواجهة Gemini البرمجية للصوت والمحادثة."
        ),
        "deliverables": "AI voice conversation\nGrammar & pronunciation feedback\nSpeech-to-text & text-to-speech\nPDF conversation reports\nAdmin dashboard & courses",
        "deliverables_ar": "محادثة صوتية بالذكاء الاصطناعي\nملاحظات حول القواعد والنطق\nتحويل الكلام إلى نص والنص إلى كلام\nتقارير المحادثات بصيغة PDF\nلوحة تحكم وإدارة الدورات",
        "gallery": [
            ("g1", "full", "About page: learning languages through AI conversations", "صفحة من نحن: تعلّم اللغات عبر محادثات بالذكاء الاصطناعي"),
            ("g2", "half", "Home page on mobile", "الصفحة الرئيسية على الهاتف"),
            ("g3", "half", "Contact page on mobile", "صفحة التواصل على الهاتف"),
        ],
    },
    {
        "slug": "maktabati-bookstore",
        "category": Category.WEB_DEVELOPMENT,
        "year": 2024,
        "featured": False,
        "order": 3,
        "live_url": "https://sleman-assaf.github.io/booksStore/",
        "repo_url": "https://github.com/Sleman-Assaf/booksStore",
        "title": "Maktabati — Online Bookstore",
        "title_ar": "مكتبتي — متجر كتب إلكتروني",
        "short": "A responsive bookstore website with featured and popular collections, special offers, articles and an app download section.",
        "short_ar": "موقع متجر كتب متجاوب يعرض الكتب المميزة والأكثر رواجًا، والعروض الخاصة، والمقالات، وقسمًا لتحميل التطبيق.",
        "description": (
            "Maktabati is a front-end bookstore experience: a hero showcase, featured books, discounted offers, a "
            "best-seller spotlight, category tabs for popular books, a newsletter sign-up and an articles section.\n\n"
            "Built with semantic HTML and custom CSS, fully responsive, and published on GitHub Pages."
        ),
        "description_ar": (
            "مكتبتي تجربة واجهة أمامية لمتجر كتب: عرض رئيسي، وكتب مميزة، وعروض بأسعار مخفّضة، وتسليط الضوء على الكتاب "
            "الأكثر مبيعًا، وتبويبات لتصنيفات الكتب الرائجة، واشتراك في النشرة البريدية، وقسم للمقالات.\n\n"
            "بُني الموقع باستخدام HTML دلالي وCSS مخصص، وهو متجاوب بالكامل ومنشور على GitHub Pages."
        ),
        "deliverables": "Responsive layout\nBook collections & offers\nCategory tabs\nNewsletter & articles\nGitHub Pages deployment",
        "deliverables_ar": "تصميم متجاوب\nمجموعات الكتب والعروض\nتبويبات التصنيفات\nالنشرة البريدية والمقالات\nالنشر على GitHub Pages",
        "gallery": [
            ("g1", "full", "Featured books and special offers", "الكتب المميزة والعروض الخاصة"),
            ("g2", "half", "Home page on mobile", "الصفحة الرئيسية على الهاتف"),
            ("g3", "half", "Featured books on mobile", "الكتب المميزة على الهاتف"),
        ],
    },
]


class Command(BaseCommand):
    help = "Add or update the GitHub portfolio projects (Nabatati, LingoVoice, Maktabati)."

    def add_arguments(self, parser):
        parser.add_argument("--media", action="store_true", help="Replace cover and gallery images.")

    def handle(self, *args, **options):
        # Real work first: move any demo samples after these projects.
        for demo in Project.objects.filter(slug__in=DEMO_SLUGS, display_order__lt=10):
            demo.display_order += 10
            demo.save(update_fields=["display_order"])

        for spec in PROJECTS:
            with transaction.atomic():
                project, created = Project.objects.update_or_create(
                    slug=spec["slug"],
                    defaults={
                        "category": spec["category"],
                        "also_in": [str(c) for c in spec.get("also_in", [])],
                        "year": spec["year"],
                        "featured": spec["featured"],
                        "display_order": spec["order"],
                        "is_published": True,
                        "cover_fit": "screen",
                        "live_url": spec["live_url"],
                        "repo_url": spec["repo_url"],
                        "title": spec["title"],
                        "title_ar": spec["title_ar"],
                        "short_description": spec["short"],
                        "short_description_ar": spec["short_ar"],
                        "description": spec["description"],
                        "description_ar": spec["description_ar"],
                        "deliverables": spec["deliverables"],
                        "deliverables_ar": spec["deliverables_ar"],
                    },
                )
                if created or options["media"] or not project.cover_image:
                    self._attach_media(project, spec)
            self.stdout.write(f"  {'+' if created else '~'} {project.title}")
        self.stdout.write(self.style.SUCCESS("GitHub projects ready."))

    def _attach_media(self, project, spec):
        folder = CONTENT / spec["slug"]
        with open(folder / "cover.jpg", "rb") as fh:
            project.cover_image.save(f"{spec['slug']}.jpg", File(fh), save=False)
        project.save()

        project.gallery.all().delete()
        for order, (key, layout, caption, caption_ar) in enumerate(spec["gallery"]):
            item = ProjectMedia(project=project, layout=layout, order=order, caption=caption, caption_ar=caption_ar)
            with open(folder / f"{key}.jpg", "rb") as fh:
                item.image.save(f"{spec['slug']}-{key}.jpg", File(fh), save=False)
            item.save()
