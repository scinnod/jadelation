# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Views for DeepL translation frontend application.

This module provides views for the translation interface and usage statistics.
"""

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

import deepl
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _

from .forms import TranslationForm
from .models import Translation, Glossary

# Configure logging
logger = logging.getLogger(__name__)


# Load configuration constants from settings (with defaults as fallback)
TRANSLATION_DETECTION_LEN = getattr(settings, 'TRANSLATION_DETECTION_LEN', 30)
STATISTICS_DAYS = getattr(settings, 'STATISTICS_DAYS', 31)
STATISTICS_MONTHS = getattr(settings, 'STATISTICS_MONTHS', 24)
STATISTICS_YEARS = getattr(settings, 'STATISTICS_YEARS', 5)


def load_glossaries():
    """
    Load active glossaries from database into a cache for use in translations.
    
    Returns:
        dict: Dictionary mapping language pairs (e.g., 'DE->EN-GB') to DeepL glossary objects
    
    Note:
        This function initializes a translator and fetches glossaries from DeepL API
        based on the glossary IDs stored in the database. Use management commands
        to manage glossaries:
        - python manage.py glossary_put <csv_file> <name> <source> <target>
        - python manage.py glossary_list
        - python manage.py glossary_remove <name_or_id>
    """
    glossary_cache = {}
    
    try:
        translator = deepl.Translator(settings.DEEPL_AUTHKEY)
        
        # Get all glossaries from database
        db_glossaries = Glossary.objects.all()
        
        for db_glossary in db_glossaries:
            try:
                # Fetch the glossary object from DeepL API
                deepl_glossary = translator.get_glossary(db_glossary.glossary_id)
                
                # Store in cache using normalised language pair as key
                # Normalise to 2-letter codes (e.g. EN-GB -> EN) so that
                # lookups from the translation view always match,
                # regardless of whether the glossary was uploaded with
                # a regional variant code or a plain language code.
                norm_source = db_glossary.source_lang[:2].upper()
                norm_target = db_glossary.target_lang[:2].upper()
                cache_key = f"{norm_source}->{norm_target}"
                glossary_cache[cache_key] = deepl_glossary
                
                logger.info(
                    f"Loaded glossary: {db_glossary.name} "
                    f"({cache_key}, {db_glossary.entry_count} entries)"
                )
            except deepl.DeepLException as e:
                logger.warning(
                    f"Could not load glossary {db_glossary.name} "
                    f"(ID: {db_glossary.glossary_id}): {e}"
                )
            except Exception as e:
                logger.exception(
                    f"Unexpected error loading glossary {db_glossary.name}: {e}"
                )
                
    except Exception as e:
        logger.error(f"Failed to initialize glossary cache: {e}")
    
    return glossary_cache


# Initialize glossaries cache (loaded on server start)
# To reload glossaries without restarting, restart the Django application
glossary = load_glossaries()


def deepl_translation(request):
    """
    Handle DeepL translation requests.
    
    Supports automatic language detection and translation between German and English.
    Logs all translations to the database for usage tracking.
    """
    if request.method == "POST":
        form = TranslationForm(request.POST)
        if form.is_valid():
            # Initial values of variables
            character_count = 0
            auto_detection = False
            
            # Initialize translator (catch configuration errors)
            try:
                translator = deepl.Translator(settings.DEEPL_AUTHKEY)
            except (AttributeError, ValueError) as e:
                logger.error(f"DeepL translator initialization failed: {e}")
                return HttpResponse(
                    _("ERROR: Translation service configuration error. Please contact the administrator.")
                )
            
            direction = form.cleaned_data["directionChoice"]

            # Perform auto detection if direction is "auto"
            if direction == "auto":
                try:
                    result = translator.translate_text(
                        form.cleaned_data["sourceText"][:TRANSLATION_DETECTION_LEN],
                        target_lang="DE",
                    )
                    character_count += min(
                        len(form.cleaned_data["sourceText"]), 
                        TRANSLATION_DETECTION_LEN
                    )
                    auto_detection = True
                    
                    if result.detected_source_lang[:2] == "DE":
                        direction = "DE->EN-GB|"
                    elif result.detected_source_lang[:2] == "EN":
                        direction = "EN-GB->DE|more"
                        
                except deepl.DeepLException as e:
                    logger.error(f"DeepL API error during auto-detection: {e}")
                    return HttpResponse(
                        _(
                            "ERROR: The API services at DeepL are currently unavailable. "
                            "Please try again later."
                        )
                    )
                except Exception as e:
                    logger.exception(f"Unexpected error during auto-detection: {e}")
                    return HttpResponse(
                        _("ERROR: An unexpected error occurred. Please try again later.")
                    )

            # Perform translation if direction known
            if direction != "auto":
                character_count += len(form.cleaned_data["sourceText"])
                
                # Parse direction string
                direction_parts = direction.split("|")
                lang_pair = direction_parts[0].split("->")
                source_lang = lang_pair[0][:2]  # Only first two letters
                target_lang = lang_pair[1]
                formality = direction_parts[1] if len(direction_parts[1]) > 0 else None
                
                # Look up glossary using normalised 2-letter codes
                # (e.g. "DE->EN" not "DE->EN-GB") to match the cache keys
                glossary_key = f"{source_lang[:2]}->{target_lang[:2]}"
                
                try:
                    result = translator.translate_text(
                        form.cleaned_data["sourceText"],
                        source_lang=source_lang,
                        target_lang=target_lang,
                        formality=formality,
                        glossary=glossary.get(glossary_key, None),
                    )
                    translation = result.text
                    
                except deepl.DeepLException as e:
                    logger.error(f"DeepL API error during translation: {e}")
                    return HttpResponse(
                        _(
                            "ERROR: The API services at DeepL are currently unavailable. "
                            "Please try again later."
                        )
                    )
                except Exception as e:
                    logger.exception(f"Unexpected error during translation: {e}")
                    return HttpResponse(
                        _("ERROR: An unexpected error occurred. Please try again later.")
                    )
            else:
                translation = _(
                    "ERROR: Language recognition was not successful. "
                    "Please provide a longer excerpt or specify the direction explicitly."
                )

            # Prepare form to return (including update of direction)
            return_form = TranslationForm(
                initial={
                    "sourceText": form.cleaned_data["sourceText"],
                    "directionChoice": direction,
                    "translatedText": translation,
                }
            )

            # Log translation metadata to database
            try:
                Translation.objects.create(
                    characters=character_count,
                    direction=direction,
                    auto_detection=auto_detection,
                )
            except Exception as e:
                logger.exception(f"Failed to log translation to database: {e}")
                # Continue - don't fail the request if logging fails

            # Request current API usage and limit
            try:
                usage = translator.get_usage()
                usage_str = _(
                    "Current total API character usage: {count} of {limit}."
                ).format(
                    count=usage.character.count, 
                    limit=usage.character.limit
                )
            except deepl.DeepLException as e:
                logger.warning(f"Could not retrieve DeepL usage statistics: {e}")
                usage_str = _(
                    "Current total API character usage: not available due to connection issues."
                )
            except Exception as e:
                logger.exception(f"Unexpected error retrieving usage stats: {e}")
                usage_str = _("Current total API character usage: not available.")

            return render(
                request,
                "translation_frontend.html",
                {"form": return_form, "usage": usage_str},
            )
        else:
            # Form is not valid - render with errors
            logger.warning(f"Invalid form submission: {form.errors}")

    # GET request or other method - create a blank form
    else:
        form = TranslationForm(initial={"directionChoice": "auto"})

    return render(
        request,
        "translation_frontend.html",
        {"form": form},
    )


def deepl_daily_statistics(request, granularity):
    """
    Display usage statistics with different granularities (daily, monthly, yearly).
    
    Args:
        request: HTTP request object
        granularity: 'd' for daily, 'm' for monthly, 'y' for yearly
    
    Returns:
        Rendered statistics page with usage data
    """
    
    def add_line(statistics, fdt, tdt):
        """Helper function to add a statistics line for a time period."""
        req = Translation.objects.filter(
            timestamp__gte=fdt, 
            timestamp__lt=tdt
        ).aggregate(cumul=Sum("characters"), events=Count("characters"))

        req_ende = Translation.objects.filter(
            direction__startswith="EN", 
            timestamp__gte=fdt, 
            timestamp__lt=tdt
        ).aggregate(cumul=Sum("characters"), events=Count("characters"))

        req_deen = Translation.objects.filter(
            direction__startswith="DE", 
            timestamp__gte=fdt, 
            timestamp__lt=tdt
        ).aggregate(cumul=Sum("characters"), events=Count("characters"))

        statistics.append(
            {
                "fdt": fdt,
                "tdt": tdt,
                "total": "{} ({})".format(
                    req["events"], 
                    req["cumul"] if req["cumul"] else 0
                ),
                "deen": "{} ({})".format(
                    req_deen["events"], 
                    req_deen["cumul"] if req_deen["cumul"] else 0
                ),
                "ende": "{} ({})".format(
                    req_ende["events"], 
                    req_ende["cumul"] if req_ende["cumul"] else 0
                ),
            }
        )

    statistics = []
    now = timezone.now()
    
    # Generate statistics based on granularity
    if granularity == "d":
        granularity_title = _("Report of daily usage:")
        dformat = "Y-m-d"
        for days in range(STATISTICS_DAYS):
            fdt = (now - relativedelta(days=days)).replace(
                minute=0, hour=0, second=0, microsecond=0
            )
            tdt = (now - relativedelta(days=(days - 1))).replace(
                minute=0, hour=0, second=0, microsecond=0
            )
            add_line(statistics, fdt, tdt)
            
    elif granularity == "m":
        granularity_title = _("Report of monthly usage:")
        dformat = "Y-m"
        for months in range(STATISTICS_MONTHS):
            fdt = (now - relativedelta(months=months)).replace(
                day=1, minute=0, hour=0, second=0, microsecond=0
            )
            tdt = (now - relativedelta(months=(months - 1))).replace(
                day=1, minute=0, hour=0, second=0, microsecond=0
            )
            add_line(statistics, fdt, tdt)
            
    elif granularity == "y":
        granularity_title = _("Report of annual usage:")
        dformat = "Y"
        for years in range(STATISTICS_YEARS):
            fdt = (now - relativedelta(years=years)).replace(
                month=1, day=1, minute=0, hour=0, second=0, microsecond=0
            )
            tdt = (now - relativedelta(years=(years - 1))).replace(
                month=1, day=1, minute=0, hour=0, second=0, microsecond=0
            )
            add_line(statistics, fdt, tdt)
    else:
        logger.warning(f"Invalid granularity requested: {granularity}")
        granularity_title = _("Requested report not available.")
        dformat = "Y-m-d"

    # Retrieve usage statistics from DeepL API
    try:
        translator = deepl.Translator(settings.DEEPL_AUTHKEY)
        usage = translator.get_usage()
        usage_str = _(
            "Current total API character usage: {count} of {limit}."
        ).format(
            count=usage.character.count, 
            limit=usage.character.limit
        )
    except deepl.DeepLException as e:
        logger.warning(f"Could not retrieve DeepL usage statistics: {e}")
        usage_str = _(
            "Current total API character usage: not available due to connection issues."
        )
    except Exception as e:
        logger.exception(f"Unexpected error retrieving usage stats: {e}")
        usage_str = _("Current total API character usage: not available.")

    return render(
        request,
        "statistics_frontend.html",
        {
            "usage": usage_str,
            "statistics": statistics,
            "granularity_title": granularity_title,
            "granularity": granularity,
            "dformat": dformat,
        },
    )
