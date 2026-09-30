from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .mailgun import MailgunError, send_inquiry
from .turnstile import verify_turnstile


def gabriel(request):
    return render(
        request,
        "datagab/gabriel.html",
        {
            "services": ContactForm.SERVICE_CHOICES,
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
    )


@require_POST
def contact(request):
    if request.POST.get("company"):
        return JsonResponse({"ok": True})

    form = ContactForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "errors": {field: errors[0] for field, errors in form.errors.items()},
            },
            status=400,
        )

    if not verify_turnstile(
        request.POST.get("cf-turnstile-response", ""),
        request.META.get("REMOTE_ADDR"),
    ):
        return JsonResponse(
            {
                "ok": False,
                "errors": {"turnstile": "Confirm you are human before sending."},
            },
            status=400,
        )

    data = form.cleaned_data
    service_label = dict(ContactForm.SERVICE_CHOICES)[data["service"]]
    try:
        send_inquiry(
            name=data["name"],
            email=data["email"],
            service=service_label,
            message=data["message"],
        )
    except MailgunError:
        return JsonResponse(
            {
                "ok": False,
                "errors": {
                    "form": "The message could not be sent. Try again in a moment.",
                },
            },
            status=502,
        )

    return JsonResponse({"ok": True})
