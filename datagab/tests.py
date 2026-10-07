import io
import tempfile
from unittest.mock import patch
from urllib.parse import parse_qs

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from datagab.mailgun import clean_name
from datagab.models import Project

MAILGUN = {
    "MAILGUN_API_KEY": "key-test",
    "MAILGUN_DOMAIN": "mg.example.com",
    "MAILGUN_API_BASE": "https://api.mailgun.net",
    "MAILGUN_FROM": "no-reply@gabesport.com",
    "CONTACT_INBOX": "hello@example.com",
    "TURNSTILE_SITE_KEY": "site-key",
    "TURNSTILE_SECRET_KEY": "secret-key",
}


@override_settings(**MAILGUN)
class ContactTests(TestCase):
    def post(self, **extra):
        data = {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "service": "web-application",
            "message": "I need a web app.",
        }
        data.update(extra)
        return self.client.post("/contact/", data)

    def test_page_includes_contact_form(self):
        response = self.client.get("/")
        self.assertContains(response, 'id="contact-form"')
        self.assertContains(response, "Web application")
        self.assertContains(response, "cf-turnstile")
        self.assertContains(response, "challenges.cloudflare.com/turnstile/v0/api.js")

    def test_rejects_invalid_email(self):
        response = self.post(email="not-an-email")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])

    @patch("datagab.views.verify_turnstile", return_value=True)
    @patch("datagab.views.send_inquiry")
    def test_sends_inquiry(self, send_inquiry, _verify_turnstile):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        send_inquiry.assert_called_once_with(
            name="Ada Lovelace",
            email="ada@example.com",
            service="Web application",
            message="I need a web app.",
        )

    @patch("datagab.views.send_inquiry")
    def test_honeypot_skips_mailgun(self, send_inquiry):
        response = self.post(company="spam")
        self.assertEqual(response.status_code, 200)
        send_inquiry.assert_not_called()

    @patch("datagab.mailgun.urllib.request.urlopen")
    def test_from_uses_gabesport_and_replies_to_client(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b'{"message":"Queued. Thank you."}'
        from datagab.mailgun import send_inquiry

        send_inquiry(
            name="Ada Lovelace",
            email="ada@example.com",
            service="Web application",
            message="I need a web app.",
        )
        request = urlopen.call_args.args[0]
        sent = parse_qs(request.data.decode())
        self.assertEqual(sent["from"], ["Ada Lovelace via Gabesport <no-reply@gabesport.com>"])
        self.assertEqual(sent["to"], ["hello@example.com"])
        self.assertEqual(sent["h:Reply-To"], ["Ada Lovelace <ada@example.com>"])

    def test_clean_name_drops_header_characters(self):
        self.assertEqual(clean_name('Ada "Lovelace" <script>'), "Ada Lovelace script")

    @patch("datagab.views.send_inquiry")
    def test_rejects_missing_turnstile(self, send_inquiry):
        response = self.post()
        self.assertEqual(response.status_code, 400)
        self.assertIn("turnstile", response.json()["errors"])
        send_inquiry.assert_not_called()

    @patch("datagab.views.verify_turnstile", return_value=True)
    @override_settings(MAILGUN_API_KEY="", MAILGUN_DOMAIN="", MAILGUN_FROM="", CONTACT_INBOX="")
    def test_missing_configuration(self, _verify_turnstile):
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.json()["ok"])


def tiny_png(name="shot.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (18, 18, 20)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PortfolioTests(TestCase):
    def test_home_links_to_portfolio(self):
        response = self.client.get("/")
        self.assertContains(response, "Work I've done")
        self.assertContains(response, 'href="/portfolio/"')

    def test_portfolio_lists_project_and_visit_link(self):
        project = Project.objects.create(
            title="name_example",
            thumbnail=tiny_png(),
            link="https://example.com",
        )
        response = self.client.get("/portfolio/")
        self.assertContains(response, "name_example")
        self.assertContains(response, "Visit site")
        self.assertContains(response, 'href="https://example.com"')
        self.assertContains(response, project.thumbnail.url)
