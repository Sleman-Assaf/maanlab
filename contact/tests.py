from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from .models import ContactMessage

VALID = {
    "name": "Layla Haddad",
    "email": "layla@example.com",
    "phone": "+962 79 000 0000",
    "company": "Example Co.",
    "service": "ai_video",
    "preferred_language": "ar",
    "message": "We need a short AI product film for a launch.",
    "website": "",
}


class ContactFormTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_valid_submission_is_stored_and_redirects(self):
        response = self.client.post("/en/contact/", VALID)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/#contact")
        message = ContactMessage.objects.get()
        self.assertEqual(message.service, "ai_video")
        self.assertEqual(message.preferred_language, "ar")
        self.assertEqual(message.submitted_from, "en")
        self.assertFalse(message.is_read)
        follow = self.client.get("/en/")
        self.assertContains(follow, "data-form-success")

    def test_arabic_submission_redirects_to_arabic_page(self):
        response = self.client.post("/ar/contact/", VALID)
        self.assertEqual(response["Location"], "/ar/#contact")
        self.assertEqual(ContactMessage.objects.get().submitted_from, "ar")

    def test_invalid_submission_shows_errors_and_keeps_values(self):
        data = {**VALID, "email": "nope", "message": "short", "service": ""}
        response = self.client.post("/en/contact/", data)
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "data-form-errors", status_code=400)
        self.assertContains(response, 'aria-invalid="true"', status_code=400)
        self.assertContains(response, 'value="Layla Haddad"', status_code=400)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_invalid_phone(self):
        response = self.client.post("/en/contact/", {**VALID, "phone": "call me maybe"})
        self.assertEqual(response.status_code, 400)

    def test_honeypot_blocks_bots(self):
        response = self.client.post("/en/contact/", {**VALID, "website": "http://spam.example"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/en/contact/", VALID)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_csrf_token_flow_works(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get("/en/")
        token = page.cookies["csrftoken"].value
        response = client.post("/en/contact/", {**VALID, "csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    @override_settings(CONTACT_RATE_LIMIT=2)
    def test_rate_limit(self):
        self.client.post("/en/contact/", VALID)
        self.client.post("/en/contact/", VALID)
        response = self.client.post("/en/contact/", VALID)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), 2)

    def test_get_redirects_to_section(self):
        response = self.client.get("/en/contact/")
        self.assertEqual(response["Location"], "/en/#contact")


class ContactAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pass-12345-word")
        self.client.force_login(self.admin)
        self.message = ContactMessage.objects.create(
            name="Omar", email="omar@example.com", service="web_development", message="Hello there, a website."
        )

    def test_changelist_lists_messages(self):
        response = self.client.get("/admin/contact/contactmessage/")
        self.assertContains(response, "Omar")
        self.assertContains(response, "omar@example.com")

    def test_search_and_filters(self):
        self.assertContains(self.client.get("/admin/contact/contactmessage/?q=omar"), "Omar")
        self.assertContains(self.client.get("/admin/contact/contactmessage/?service__exact=web_development"), "Omar")
        self.assertContains(self.client.get("/admin/contact/contactmessage/?is_read__exact=0"), "Omar")

    def test_opening_a_message_marks_it_read(self):
        self.client.get(f"/admin/contact/contactmessage/{self.message.pk}/change/")
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)

    def test_mark_unread_action(self):
        ContactMessage.objects.update(is_read=True)
        self.client.post(
            "/admin/contact/contactmessage/",
            {"action": "mark_unread", "_selected_action": [self.message.pk]},
        )
        self.message.refresh_from_db()
        self.assertFalse(self.message.is_read)

    def test_project_admin_pages(self):
        self.assertEqual(self.client.get("/admin/projects/project/").status_code, 200)
        self.assertEqual(self.client.get("/admin/projects/project/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/core/heromedia/add/").status_code, 200)
