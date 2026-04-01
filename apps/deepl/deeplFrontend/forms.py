# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TranslationForm(forms.Form):
    DIRECTION_CHOICES = [
        ("auto", _("auto detection")),
        ("DE->EN-GB|", _("German -> English")),
        ("EN-GB->DE|more", _("English -> German (formal)")),
        ("EN-GB->DE|less", _("English -> German (less formal)")),
    ]
    sourceText = forms.CharField(required=True, widget=forms.Textarea, label=_("Text for translation"))
    directionChoice = forms.ChoiceField(required=True, choices=DIRECTION_CHOICES, label=_("Direction of translation"))
    translatedText = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.Textarea,
        label=_("DeepL translation"),
    )

    def clean_sourceText(self):
        text = self.cleaned_data["sourceText"]
        max_len = getattr(settings, "MAX_TRANSLATION_LENGTH", 0)
        if max_len > 0 and len(text) > max_len:
            raise forms.ValidationError(
                _("The text exceeds the maximum allowed length of %(limit)s characters (currently %(length)s characters)."),
                code="max_length",
                params={"limit": max_len, "length": len(text)},
            )
        return text
