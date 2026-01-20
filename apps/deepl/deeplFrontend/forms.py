# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences

from django import forms
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
