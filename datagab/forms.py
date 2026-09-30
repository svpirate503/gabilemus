from django import forms


class ContactForm(forms.Form):
    SERVICE_CHOICES = [
        ("web-application", "Web application"),
        ("api-backend", "API and backend"),
        ("consulting", "Consulting"),
    ]

    name = forms.CharField(max_length=120, strip=True)
    email = forms.EmailField(max_length=254)
    service = forms.ChoiceField(choices=SERVICE_CHOICES)
    message = forms.CharField(max_length=4000, strip=True)

    def clean_name(self):
        name = self.cleaned_data["name"].replace("\r", " ").replace("\n", " ")
        if not name.strip():
            raise forms.ValidationError("Enter your name.")
        return " ".join(name.split())

    def clean_message(self):
        message = self.cleaned_data["message"].replace("\r\n", "\n").replace("\r", "\n")
        if not message.strip():
            raise forms.ValidationError("Tell me a little about the project.")
        return message.strip()
