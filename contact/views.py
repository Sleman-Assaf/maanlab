import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from core.i18n import current_language
from core.views import render_home

from .forms import ContactForm

logger = logging.getLogger("maanlab")


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "unknown")


def _rate_limited(request) -> bool:
    key = f"contact-rate:{_client_ip(request)}"
    count = cache.get(key, 0)
    if count >= settings.CONTACT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, settings.CONTACT_RATE_WINDOW_SECONDS)
    return False


def _notify(message) -> None:
    if not settings.CONTACT_NOTIFY_EMAIL:
        return
    body = (
        f"Name: {message.name}\nEmail: {message.email}\nPhone: {message.phone}\n"
        f"Company: {message.company}\nService: {message.get_service_display()}\n"
        f"Preferred language: {message.preferred_language}\n\n{message.message}"
    )
    try:
        send_mail(
            f"[MAAN LAB] New inquiry — {message.name}",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_NOTIFY_EMAIL],
            fail_silently=False,
        )
    except Exception:  # noqa: BLE001 — never lose an inquiry over email
        logger.exception("Could not send contact notification")


@require_http_methods(["GET", "POST"])
def submit(request):
    home_url = reverse("core:home")
    if request.method == "GET":
        return redirect(f"{home_url}#contact")

    form = ContactForm(request.POST, language=current_language())

    if _rate_limited(request):
        form.is_valid()
        form.add_error(None, _("Too many messages from this connection. Please try again in a few minutes."))
        return render_home(request, contact_form=form, status=429)

    if form.is_valid():
        message = form.save(commit=False)
        message.submitted_from = current_language()
        message.save()
        _notify(message)
        messages.success(
            request,
            _("Thanks — we got your message. We'll get back to you soon."),
            extra_tags="contact",
        )
        return redirect(f"{home_url}#contact")

    return render_home(request, contact_form=form, status=400)
