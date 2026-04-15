# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences

import os

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


# Allowed file extensions for document translation
ALLOWED_DOC_EXTENSIONS = (".docx", ".pptx")


class DocumentTranslationForm(forms.Form):
    """Form for uploading .docx / .pptx files for in-place translation."""

    DIRECTION_CHOICES = [
        ("", _("— Please select —")),
        ("DE->EN-GB|", _("German -> English")),
        ("EN-GB->DE|more", _("English -> German (formal)")),
        ("EN-GB->DE|less", _("English -> German (less formal)")),
    ]

    directionChoice = forms.ChoiceField(
        required=True,
        choices=DIRECTION_CHOICES,
        label=_("Direction of translation"),
    )

    document = forms.FileField(
        required=True,
        label=_("Document (.docx or .pptx)"),
        help_text=_("Upload a Word or PowerPoint file. The document structure and formatting will be preserved as far as possible."),
    )

    def clean_document(self):
        uploaded = self.cleaned_data["document"]
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in ALLOWED_DOC_EXTENSIONS:
            raise forms.ValidationError(
                _("Unsupported file type '%(ext)s'. Please upload a .docx or .pptx file."),
                code="invalid_extension",
                params={"ext": ext},
            )
        max_mb = getattr(settings, "MAX_DOCUMENT_SIZE_MB", 50)
        max_size = max_mb * 1024 * 1024
        if uploaded.size > max_size:
            raise forms.ValidationError(
                _("The file is too large (%(size)s MB). Maximum allowed size is %(limit)s MB."),
                code="file_too_large",
                params={"size": round(uploaded.size / (1024 * 1024), 1), "limit": max_mb},
            )
        return uploaded
