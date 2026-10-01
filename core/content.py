"""
Static homepage content (interface copy lives in the translation catalog).

Service visuals are placeholders in /static/img/services/ and
/static/video/ — replace the files to update the site.
"""
from django.utils.translation import gettext_lazy as _

SERVICES = [
    {
        "key": "ai_automation",
        "number": "01",
        "title": _("AI & Automation"),
        "summary": _(
            "We remove repetitive work, connect your tools and build AI-powered workflows "
            "that save time and reduce manual steps."
        ),
        "examples": [
            _("Excel automation"),
            _("Automated reporting"),
            _("Workflow automation"),
            _("API integration"),
            _("AI agents"),
            _("Arabic AI call center"),
        ],
        "media": {"type": "image", "src": "img/services/automation.svg"},
        "caption": _("From spreadsheet to report to inbox — automatically"),
    },
    {
        "key": "web_development",
        "number": "02",
        "title": _("Web Development"),
        "summary": _(
            "Websites, platforms and internal tools built to be fast, clear, bilingual "
            "and easy to manage."
        ),
        "examples": [
            _("Corporate websites"),
            _("Landing pages"),
            _("Web applications"),
            _("Custom platforms"),
            _("Internal business systems"),
            _("Responsive interfaces"),
        ],
        "media": {"type": "image", "src": "img/services/web.svg"},
        "caption": _("Clear interfaces, structured systems, smooth experiences"),
    },
    {
        "key": "ai_video",
        "number": "03",
        "title": _("AI Video Generation"),
        "summary": _(
            "Commercials, product films and social content created with AI — from concept "
            "and storyboard to the final edit."
        ),
        "examples": [
            _("AI commercials"),
            _("Product films"),
            _("Social media campaigns"),
            _("Cinematic brand videos"),
            _("Concept development"),
            _("Storyboarding"),
            _("AI visual production"),
        ],
        "media": {
            "type": "video",
            "src": "video/ai-film-services.mp4",
            "src_mobile": "video/ai-film-services-mobile.mp4",
            "poster": "video/ai-film-services.webp",
        },
        "caption": _("An AI-made airline film — from the cabin to Petra"),
    },
    {
        "key": "digital_transformation",
        "number": "04",
        "title": _("Digital Transformation"),
        "summary": _(
            "We turn scattered spreadsheets, manual processes and disconnected tools into "
            "systems your team can actually run."
        ),
        "examples": [
            _("Digitizing manual workflows"),
            _("Business process redesign"),
            _("Replacing spreadsheets with systems"),
            _("Internal platforms"),
            _("System integration"),
            _("Dashboards"),
            _("Operational automation"),
        ],
        "media": {"type": "image", "src": "img/services/transformation.svg"},
        "caption": _("From scattered tools to one connected workflow"),
    },
]

ABOUT_KEYWORDS = [
    _("Technology"),
    _("Engineering"),
    _("Automation"),
    _("Creative thinking"),
    _("AI production"),
]
