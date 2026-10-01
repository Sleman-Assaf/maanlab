import re

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, LanguageChoice

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


class ContactForm(forms.ModelForm):
    # Honeypot: real people never see or fill this field.
    website = forms.CharField(required=False, label=_("Leave this field empty"))

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "company", "service", "preferred_language", "message"]
        labels = {
            "name": _("Name"),
            "email": _("Email"),
            "phone": _("Phone"),
            "company": _("Company / Business"),
            "service": _("Service"),
            "preferred_language": _("Preferred language"),
            "message": _("Message"),
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 120}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "dir": "ltr", "spellcheck": "false"}),
            "phone": forms.TextInput(
                attrs={"autocomplete": "tel", "inputmode": "tel", "dir": "ltr", "type": "tel"}
            ),
            "company": forms.TextInput(attrs={"autocomplete": "organization"}),
            "service": forms.Select(),
            "preferred_language": forms.RadioSelect(),
            "message": forms.Textarea(attrs={"rows": 5, "maxlength": 5000}),
        }
        error_messages = {
            "name": {"required": _("Please tell us your name.")},
            "email": {"required": _("Please add an email address."), "invalid": _("That email address doesn't look right.")},
            "service": {"required": _("Choose the service you're interested in.")},
            "message": {"required": _("Tell us a little about the project.")},
        }

    def __init__(self, *args, language: str = "en", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].choices = [("", _("Select a service"))] + list(
            self.fields["service"].choices
        )[1:]
        self.fields["preferred_language"].choices = LanguageChoice.choices
        if not self.is_bound:
            self.initial.setdefault("preferred_language", language if language in ("en", "ar") else "en")
        self.fields["website"].widget.attrs.update({"tabindex": "-1", "autocomplete": "off"})

    def full_clean(self):
        super().full_clean()
        # Link invalid inputs to their error message for assistive technology.
        for name in self.errors:
            if name in self.fields:
                attrs = self.fields[name].widget.attrs
                attrs["aria-invalid"] = "true"
                attrs["aria-describedby"] = f"{self[name].auto_id}-error"

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError(_("Please enter your full name."))
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not PHONE_RE.match(phone):
            raise forms.ValidationError(_("Use digits only, with an optional + country code."))
        return phone

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError(_("A little more detail helps — at least 10 characters."))
        return message

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(_("Spam protection triggered."))
        return ""
