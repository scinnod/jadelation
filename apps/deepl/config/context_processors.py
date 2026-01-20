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
    """
    # Get current language
    lang = get_language()
    if lang:
        lang = lang.split('-')[0]  # Convert 'en-us' to 'en'
    else:
        lang = 'en'
    
    # Select language-specific APP_TITLE
    if lang == 'de':
        app_title = settings.APP_TITLE_DE
    else:
        app_title = settings.APP_TITLE_EN
    
    # Select language-specific ORGANIZATION_NAME
    if lang == 'de':
        organization_name = settings.ORGANIZATION_NAME_DE
    else:
        organization_name = settings.ORGANIZATION_NAME_EN
    
    # Replace {year} placeholder with current year
    footer_text = settings.FOOTER_TEXT.replace('{year}', str(datetime.now().year))
    
    return {
        'APP_TITLE': app_title,
        'ORGANIZATION_NAME': organization_name,
        'FOOTER_TEXT': footer_text,
        'LOGO_FILENAME': settings.LOGO_FILENAME,
        'LOGO_MAX_WIDTH': settings.LOGO_MAX_WIDTH,
        'PRIMARY_COLOR': settings.PRIMARY_COLOR,
        'SECONDARY_COLOR': settings.SECONDARY_COLOR,
    }
