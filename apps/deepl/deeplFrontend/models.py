# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Models for DeepL translation frontend application.

This module defines the database models for tracking translations and glossaries.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Translation(models.Model):
    """
    Track individual translation requests for usage statistics.
    
    Records metadata about each translation including character count,
    language direction, and whether auto-detection was used.
    """
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Time stamp")
    )
    characters = models.IntegerField(
        verbose_name=_("Characters sent to DeepL for translation")
    )
    direction = models.CharField(
        max_length=20, 
        verbose_name=_("Direction of Translation after auto detection")
    )
    auto_detection = models.BooleanField(
        verbose_name=_("Auto detection of language used?")
    )

    class Meta:
        verbose_name = _("Translation")
        verbose_name_plural = _("Translations")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["direction"]),
        ]

    def __str__(self):
        return f"{self.direction} - {self.timestamp}"


class Glossary(models.Model):
    """
    Track DeepL glossaries uploaded to the API.
    
    Stores metadata about glossaries including the DeepL glossary ID,
    original filename, languages, and custom comments for easy management.
    """
    glossary_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("DeepL Glossary ID"),
        help_text=_("The unique identifier returned by DeepL API")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Glossary Name"),
        help_text=_("Human-readable name for the glossary")
    )
    source_lang = models.CharField(
        max_length=10,
        verbose_name=_("Source Language"),
        help_text=_("Source language code (e.g., DE, EN)")
    )
    target_lang = models.CharField(
        max_length=10,
        verbose_name=_("Target Language"),
        help_text=_("Target language code (e.g., EN-GB, DE)")
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Upload Date"),
        help_text=_("When the glossary was uploaded to DeepL")
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_("Original Filename"),
        help_text=_("The original CSV filename")
    )
    comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Comment"),
        help_text=_("Optional description or notes about this glossary")
    )
    entry_count = models.IntegerField(
        default=0,
        verbose_name=_("Entry Count"),
        help_text=_("Number of entries in the glossary")
    )

    class Meta:
        verbose_name = _("Glossary")
        verbose_name_plural = _("Glossaries")
        ordering = ["-upload_date"]
        indexes = [
            models.Index(fields=["glossary_id"]),
            models.Index(fields=["source_lang", "target_lang"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.source_lang}->{self.target_lang})"

    @property
    def language_pair(self):
        """Return the language pair in format 'SOURCE->TARGET'."""
        return f"{self.source_lang}->{self.target_lang}"
