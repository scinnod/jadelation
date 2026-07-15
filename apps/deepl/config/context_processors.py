# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Context processors for DeepL Translation Frontend.

This module provides custom context processors that make settings
available to all templates.
"""

from datetime import datetime
from django.conf import settings
from django.utils.translation import get_language


def _get_localised(mapping, fallback=""):
    """Pick the value for the current language from *mapping*.

    Fallback chain:
      1. Exact 2-letter language code (e.g. ``de``)
      2. Django's ``LANGUAGE_CODE`` setting (normalised, e.g. ``en``)
      3. ``"en"`` as ultimate default
      4. First available value in the dict
      5. *fallback* string
    """
    if not mapping:
        return fallback

    lang = get_language()
    if lang:
        lang = lang.split("-")[0].lower()
    else:
        lang = None

    # Try current language
    if lang and lang in mapping:
        return mapping[lang]

    # Try configured default language
    default_lang = getattr(settings, "LANGUAGE_CODE", "en-us").split("-")[0].lower()
    if default_lang in mapping:
        return mapping[default_lang]

    # Try English
    if "en" in mapping:
        return mapping["en"]

    # Return any value that exists
    for value in mapping.values():
        if value:
            return value

    return fallback


def app_settings(request):
    """
    Add application settings to template context.

    Makes branding and configuration settings available in all templates
    without needing to pass them explicitly in every view.

    Automatically selects language-specific versions based on current language.

    Available template variables:
        - APP_TITLE: Application title for browser tab (language-specific)
        - ORGANIZATION_NAME: Organization name for footer (language-specific)
        - FOOTER_TEXT: Footer text with {year} replaced by current year
        - LOGO_FILENAME: Logo filename (if configured)
        - LOGO_MAX_WIDTH: Maximum logo width in pixels
        - PRIMARY_COLOR: Primary brand color (hex code without #)
        - SECONDARY_COLOR: Secondary brand color (hex code without #)
        - SSO_LOGOUT_URL: URL for SSO logout (if configured, enables logout button)
    """
    # Select language-specific values via fallback chain
    app_title = _get_localised(settings.APP_TITLE)
    organization_name = _get_localised(settings.ORGANIZATION_NAME)

    # Replace {year} placeholder with current year
    footer_text = settings.FOOTER_TEXT.replace('{year}', str(datetime.now().year))

    # Resolve document-translation feature flag (False / True / regex string)
    val = getattr(settings, 'DOCUMENT_TRANSLATION_ENABLED', False)
    if val is False:
        doc_trans_enabled = False
        doc_notice = ""
    elif val is True:
        doc_trans_enabled = True
        doc_notice = ""  # everyone has access — no notice needed
    else:  # regex string — check session flag set by DocumentTranslationsMiddleware
        doc_trans_enabled = bool(request.session.get('document_translations', False))
        # Only show notice to users who actually have access in regex mode
        if doc_trans_enabled:
            doc_notice = _get_localised(getattr(settings, 'DOCUMENT_TRANSLATION_NOTICE', {}))
        else:
            doc_notice = ""

    return {
        'APP_TITLE': app_title,
        'ORGANIZATION_NAME': organization_name,
        'FOOTER_TEXT': footer_text,
        'LOGO_FILENAME': settings.LOGO_FILENAME,
        'LOGO_MAX_WIDTH': settings.LOGO_MAX_WIDTH,
        'PRIMARY_COLOR': settings.PRIMARY_COLOR,
        'SECONDARY_COLOR': settings.SECONDARY_COLOR,
        'SSO_LOGOUT_URL': settings.SSO_LOGOUT_URL,
        'MAX_TRANSLATION_LENGTH': getattr(settings, 'MAX_TRANSLATION_LENGTH', 0),
        'MAX_DOCUMENT_SIZE_MB': getattr(settings, 'MAX_DOCUMENT_SIZE_MB', 50),
        'DOCUMENT_TRANSLATION_ENABLED': doc_trans_enabled,
        'DOCUMENT_TRANSLATION_NOTICE': doc_notice,
        # Resolved fair-use text for the current language (empty string when the
        # operator has cleared all language variants → template hides the checkbox).
        'DOCUMENT_TRANSLATION_FAIR_USE_TEXT': _get_localised(
            getattr(settings, 'DOCUMENT_TRANSLATION_FAIR_USE_TEXT', {})
        ),
    }
