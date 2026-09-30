import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode

from django.conf import settings

logger = logging.getLogger(__name__)


class MailgunError(Exception):
    pass


def clean_name(name):
    return " ".join(name.replace("<", "").replace(">", "").replace('"', "").split())


def send_inquiry(*, name, email, service, message):
    missing = [
        key
        for key, value in {
            "MAILGUN_API_KEY": settings.MAILGUN_API_KEY,
            "MAILGUN_DOMAIN": settings.MAILGUN_DOMAIN,
            "MAILGUN_FROM": settings.MAILGUN_FROM,
            "CONTACT_INBOX": settings.CONTACT_INBOX,
        }.items()
        if not value
    ]
    if missing:
        raise MailgunError("Mailgun is not configured.")

    safe_name = clean_name(name)
    payload = urllib.parse.urlencode(
        {
            "from": f"{safe_name} via Gabesport <{settings.MAILGUN_FROM}>",
            "to": settings.CONTACT_INBOX,
            "subject": f"Project inquiry from {safe_name}",
            "text": (
                f"Name: {safe_name}\n"
                f"Email: {email}\n"
                f"Service: {service}\n\n"
                f"{message}"
            ),
            "h:Reply-To": f"{safe_name} <{email}>",
        }
    ).encode()
    token = b64encode(f"api:{settings.MAILGUN_API_KEY}".encode()).decode()
    url = f"{settings.MAILGUN_API_BASE}/v3/{settings.MAILGUN_DOMAIN}/messages"
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Basic {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        logger.error("Mailgun rejected the contact message: %s", detail)
        raise MailgunError(detail or "Mailgun rejected the message.") from exc
    except urllib.error.URLError as exc:
        logger.error("Mailgun could not be reached: %s", exc.reason)
        raise MailgunError("Could not reach Mailgun.") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}
