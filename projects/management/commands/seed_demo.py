"""
Create sample projects so the site (and the project filter) can be tested
immediately. Everything created here is clearly labelled as a sample and
uses placeholder media — replace it from the Django admin.

    python manage.py seed_demo            # create missing samples
    python manage.py seed_demo --media    # also regenerate placeholder media
    python manage.py seed_demo --delete   # remove all sample projects
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Category, Project, ProjectMedia
from projects.placeholders import render

VIDEO_DIR = Path(settings.BASE_DIR) / "static" / "video"

SAMPLES = [
    {
        "slug": "sandstone-product-film",
        "category": Category.AI_VIDEO,
        "year": 2026,
        "featured": True,
        "order": 1,
        "video": "clip-sand.mp4",
        "title": "Sandstone — AI Product Film",
        "title_ar": "ساندستون — فيلم منتج بالذكاء الاصطناعي",
        "client": "Sample client · Specialty coffee",
        "client_ar": "عميل تجريبي · قهوة مختصة",
        "short": "A 30-second product film generated and graded with AI — from moodboard to final cut in two weeks.",
        "short_ar": "فيلم منتج مدته ٣٠ ثانية، مولَّد ومعالج لونياً بالذكاء الاصطناعي — من لوحة الإلهام إلى النسخة النهائية خلال أسبوعين.",
        "description": (
            "The brief was simple: a premium film for a new roast, without the cost of a full studio shoot.\n\n"
            "We wrote the concept, built a storyboard, and generated every shot with AI image and video tools — "
            "then edited, scored and colour-graded the film in-house. Cut-downs for Reels and Stories were "
            "delivered alongside the master.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "كان المطلوب واضحاً: فيلم فاخر لمنتج قهوة جديد، دون تكلفة تصوير كامل في استوديو.\n\n"
            "كتبنا الفكرة وبنينا لوحة القصة، وولّدنا كل لقطة بأدوات الصور والفيديو بالذكاء الاصطناعي، "
            "ثم أنجزنا المونتاج والموسيقى والمعالجة اللونية داخلياً، مع نسخ قصيرة لمنصات التواصل.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "Concept & storyboard\nAI image & video generation\nEdit, sound & grade\nSocial cut-downs",
        "deliverables_ar": "الفكرة ولوحة القصة\nتوليد الصور والفيديو\nالمونتاج والصوت والتلوين\nنسخ لمنصات التواصل",
    },
    {
        "slug": "monthly-reporting-automated",
        "category": Category.AI_AUTOMATION,
        "year": 2026,
        "order": 2,
        "title": "Monthly Reporting, Automated",
        "title_ar": "تقارير شهرية مؤتمتة",
        "client": "Sample client · Logistics",
        "client_ar": "عميل تجريبي · خدمات لوجستية",
        "short": "Twelve spreadsheets and two days of copy-paste replaced by a pipeline that emails the report at 7am.",
        "short_ar": "اثنا عشر ملف Excel ويومان من النسخ واللصق، استُبدلت بمسار آلي يرسل التقرير بالبريد عند السابعة صباحاً.",
        "description": (
            "Every month, the operations team merged exports from four systems by hand. Errors were common and the "
            "report arrived late.\n\n"
            "We connected the sources through their APIs, cleaned and validated the data automatically, and generated "
            "a formatted Excel and PDF report that is emailed to management on schedule.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "كان فريق العمليات يدمج بيانات أربعة أنظمة يدوياً كل شهر، فتكثر الأخطاء ويتأخر التقرير.\n\n"
            "ربطنا المصادر عبر واجهاتها البرمجية، ونظّفنا البيانات وتحققنا منها آلياً، وأنشأنا تقرير Excel وPDF "
            "منسقاً يصل إلى الإدارة بالبريد في موعده.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "API integration\nData validation\nExcel & PDF generation\nScheduled delivery",
        "deliverables_ar": "ربط الواجهات البرمجية\nالتحقق من البيانات\nإنشاء ملفات Excel وPDF\nإرسال مجدول",
    },
    {
        "slug": "bilingual-corporate-platform",
        "category": Category.WEB_DEVELOPMENT,
        "year": 2025,
        "order": 3,
        "title": "Bilingual Corporate Platform",
        "title_ar": "منصة مؤسسية ثنائية اللغة",
        "client": "Sample client · Engineering firm",
        "client_ar": "عميل تجريبي · شركة هندسية",
        "short": "An Arabic-first, fully RTL corporate site with a project library the team updates themselves.",
        "short_ar": "موقع مؤسسي يبدأ بالعربية ويدعم الاتجاه من اليمين لليسار بالكامل، مع مكتبة مشاريع يحدّثها الفريق بنفسه.",
        "description": (
            "The firm needed a site that felt as considered in Arabic as in English — not a translated afterthought.\n\n"
            "We designed both languages together, built the platform on Django with server-side rendering for speed "
            "and SEO, and gave the team a simple admin to publish projects and news.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "احتاجت الشركة موقعاً يبدو متقناً بالعربية كما بالإنجليزية — لا ترجمة لاحقة.\n\n"
            "صممنا اللغتين معاً، وبنينا المنصة على Django مع العرض من الخادم للسرعة وتحسين الظهور في محركات البحث، "
            "ومنحنا الفريق لوحة إدارة بسيطة لنشر المشاريع والأخبار.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "UX & interface design\nArabic/English content structure\nDjango platform\nSEO setup",
        "deliverables_ar": "تصميم التجربة والواجهة\nهيكلة المحتوى بالعربية والإنجليزية\nمنصة Django\nإعداد تحسين محركات البحث",
    },
    {
        "slug": "from-spreadsheets-to-system",
        "category": Category.DIGITAL_TRANSFORMATION,
        "year": 2025,
        "featured": True,
        "order": 4,
        "title": "From Spreadsheets to One System",
        "title_ar": "من جداول متفرقة إلى نظام واحد",
        "client": "Sample client · Distribution company",
        "client_ar": "عميل تجريبي · شركة توزيع",
        "short": "Orders, stock and delivery moved from scattered sheets and WhatsApp into one internal platform with live dashboards.",
        "short_ar": "نقل الطلبات والمخزون والتوصيل من جداول متفرقة ورسائل واتساب إلى منصة داخلية واحدة بلوحات متابعة مباشرة.",
        "description": (
            "Work lived in dozens of spreadsheets and group chats. Nobody had a reliable view of stock or open orders.\n\n"
            "We mapped the real process with the team, redesigned it, and replaced the sheets with an internal "
            "platform: order entry, stock movements, delivery status and a management dashboard.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "كان العمل موزعاً على عشرات الجداول ومجموعات المحادثة، ولم تكن هناك صورة موثوقة للمخزون أو الطلبات المفتوحة.\n\n"
            "رسمنا العملية الفعلية مع الفريق وأعدنا تصميمها، واستبدلنا الجداول بمنصة داخلية تشمل إدخال الطلبات "
            "وحركة المخزون وحالة التوصيل ولوحة متابعة للإدارة.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "Process mapping & redesign\nInternal platform\nDashboards\nTeam onboarding",
        "deliverables_ar": "رسم العمليات وإعادة تصميمها\nمنصة داخلية\nلوحات متابعة\nتدريب الفريق",
    },
    {
        "slug": "night-market-campaign",
        "category": Category.AI_VIDEO,
        "year": 2025,
        "order": 5,
        "video": "clip-night.mp4",
        "title": "Night Market — Social Campaign",
        "title_ar": "سوق الليل — حملة تواصل اجتماعي",
        "client": "Sample client · Retail brand",
        "client_ar": "عميل تجريبي · علامة تجارية للتجزئة",
        "short": "A six-part AI video series for a Ramadan night-market launch, cut for vertical and horizontal feeds.",
        "short_ar": "سلسلة من ستة مقاطع فيديو بالذكاء الاصطناعي لإطلاق سوق ليلي في رمضان، بنسخ عمودية وأفقية.",
        "description": (
            "The brand wanted a campaign that felt cinematic but could be produced fast and adapted per channel.\n\n"
            "We developed a visual world, generated the series with AI, and delivered each film in multiple formats "
            "with Arabic typography designed for motion.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "أرادت العلامة حملة بطابع سينمائي يمكن إنتاجها بسرعة وتكييفها لكل منصة.\n\n"
            "طوّرنا عالماً بصرياً، وولّدنا السلسلة بالذكاء الاصطناعي، وسلّمنا كل فيلم بعدة مقاسات مع طباعة عربية "
            "مصممة للحركة.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "Campaign concept\nAI video series\nArabic motion typography\nMulti-format delivery",
        "deliverables_ar": "فكرة الحملة\nسلسلة فيديو بالذكاء الاصطناعي\nطباعة عربية متحركة\nتسليم بعدة مقاسات",
    },
    {
        "slug": "arabic-ai-call-assistant",
        "category": Category.AI_AUTOMATION,
        "year": 2026,
        "order": 6,
        "title": "Arabic AI Call Assistant",
        "title_ar": "مساعد اتصال عربي بالذكاء الاصطناعي",
        "client": "Sample client · Service center",
        "client_ar": "عميل تجريبي · مركز خدمة",
        "short": "A voice agent that answers routine calls in Jordanian Arabic and hands complex cases to a person.",
        "short_ar": "وكيل صوتي يجيب على الاتصالات الروتينية باللهجة الأردنية ويحوّل الحالات المعقدة إلى موظف.",
        "description": (
            "Most calls asked the same five questions. Staff spent their day repeating answers instead of solving problems.\n\n"
            "We built an AI call assistant that understands Jordanian Arabic, answers common requests, books "
            "appointments and passes the rest to the team with a written summary.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "كانت معظم الاتصالات تطرح الأسئلة الخمسة نفسها، فيقضي الموظفون يومهم في تكرار الإجابات بدلاً من حل المشكلات.\n\n"
            "بنينا مساعد اتصال بالذكاء الاصطناعي يفهم اللهجة الأردنية، ويجيب على الطلبات الشائعة، ويحجز المواعيد، "
            "ويحوّل بقية الحالات إلى الفريق مع ملخص مكتوب.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "Conversation design\nVoice AI agent\nBooking integration\nHandover to staff",
        "deliverables_ar": "تصميم المحادثة\nوكيل صوتي ذكي\nربط الحجوزات\nتحويل إلى الموظفين",
    },
    {
        "slug": "clinic-booking-web-app",
        "category": Category.WEB_DEVELOPMENT,
        "year": 2025,
        "order": 7,
        "title": "Clinic Booking Web App",
        "title_ar": "تطبيق ويب لحجز المواعيد",
        "client": "Sample client · Clinic group",
        "client_ar": "عميل تجريبي · مجموعة عيادات",
        "short": "A fast, mobile-first booking app for four clinics, with reminders and a simple staff dashboard.",
        "short_ar": "تطبيق حجز سريع مصمم للهاتف أولاً لأربع عيادات، مع تذكيرات ولوحة بسيطة للموظفين.",
        "description": (
            "Patients booked by phone during working hours only. Missed calls meant missed appointments.\n\n"
            "We built a mobile-first web app for booking in Arabic or English, automatic SMS reminders, and a "
            "dashboard for reception staff to manage the day.\n\n"
            "Sample case study — placeholder content and media."
        ),
        "description_ar": (
            "كان المرضى يحجزون هاتفياً خلال ساعات الدوام فقط، والمكالمات الفائتة تعني مواعيد ضائعة.\n\n"
            "بنينا تطبيق ويب للحجز بالعربية أو الإنجليزية، مع تذكيرات تلقائية بالرسائل القصيرة ولوحة لموظفي "
            "الاستقبال لإدارة اليوم.\n\n"
            "دراسة حالة تجريبية — محتوى ووسائط مؤقتة."
        ),
        "deliverables": "Product design\nWeb application\nSMS reminders\nStaff dashboard",
        "deliverables_ar": "تصميم المنتج\nتطبيق ويب\nتذكيرات بالرسائل\nلوحة للموظفين",
    },
]


class Command(BaseCommand):
    help = "Create clearly-labelled sample projects with placeholder media."

    def add_arguments(self, parser):
        parser.add_argument("--media", action="store_true", help="Regenerate placeholder media for existing samples.")
        parser.add_argument("--delete", action="store_true", help="Delete all sample projects.")

    def handle(self, *args, **options):
        slugs = [s["slug"] for s in SAMPLES]
        if options["delete"]:
            deleted, _ = Project.objects.filter(slug__in=slugs).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} sample object(s)."))
            return

        for index, spec in enumerate(SAMPLES):
            with transaction.atomic():
                project, created = Project.objects.update_or_create(
                    slug=spec["slug"],
                    defaults={
                        "category": spec["category"],
                        "year": spec["year"],
                        "featured": spec.get("featured", False),
                        "display_order": spec["order"],
                        "is_published": True,
                        "title": spec["title"],
                        "title_ar": spec["title_ar"],
                        "client": spec["client"],
                        "client_ar": spec["client_ar"],
                        "short_description": spec["short"],
                        "short_description_ar": spec["short_ar"],
                        "description": spec["description"],
                        "description_ar": spec["description_ar"],
                        "deliverables": spec["deliverables"],
                        "deliverables_ar": spec["deliverables_ar"],
                    },
                )
                if created or options["media"] or not project.cover_image:
                    self._attach_media(project, spec, seed=index * 17 + 3)
            self.stdout.write(f"  {'+' if created else '~'} {project.title}")

        self.stdout.write(self.style.SUCCESS(f"{len(SAMPLES)} sample projects ready."))

    def _attach_media(self, project, spec, seed):
        label = spec["title"].split("—")[0].strip()
        project.cover_image.save(
            f"{project.slug}.jpg", ContentFile(render(project.category, label, seed)), save=False
        )
        if spec.get("video"):
            with open(VIDEO_DIR / spec["video"], "rb") as fh:
                project.cover_video.save(f"{project.slug}.mp4", File(fh), save=False)
        project.save()

        project.gallery.all().delete()
        layouts = [ProjectMedia.Layout.FULL, ProjectMedia.Layout.HALF, ProjectMedia.Layout.HALF]
        captions = [
            ("Placeholder — key visual", "صورة مؤقتة — المشهد الرئيسي"),
            ("Placeholder — detail", "صورة مؤقتة — تفصيل"),
            ("Placeholder — system", "صورة مؤقتة — النظام"),
        ]
        for order, (layout, (caption, caption_ar)) in enumerate(zip(layouts, captions)):
            size = (2400, 1500) if layout == ProjectMedia.Layout.FULL else (1400, 1750)
            item = ProjectMedia(project=project, layout=layout, order=order, caption=caption, caption_ar=caption_ar)
            item.image.save(
                f"{project.slug}-{order}.jpg",
                ContentFile(render(project.category, f"{label} {order + 1:02d}", seed + order + 1, size=size)),
                save=False,
            )
            item.save()
