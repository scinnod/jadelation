# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Models for DeepL translation frontend application.

This module defines the database models for tracking translations and glossaries.
"""

import uuid

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
    is_document_translation = models.BooleanField(
        default=False,
        verbose_name=_("Document translation?"),
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


class DocumentTranslationJob(models.Model):
    """Track an asynchronous document translation job.

    Stores metadata about the upload, translation progress, and the
    resulting file.  The translated file is stored on disk inside
    ``settings.MEDIA_ROOT / 'doc_translations'`` and removed once
    downloaded (or after 10 minutes if never downloaded).
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    session_key = models.CharField(
        max_length=40,
        verbose_name=_("Session key"),
        help_text=_("Django session key of the user who started the job"),
        db_index=True,
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Status"),
    )
    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Error message"),
    )

    # Upload metadata
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_("Original filename"),
    )
    file_type = models.CharField(
        max_length=10,
        verbose_name=_("File type"),
        help_text=_("Extension, e.g. .docx or .pptx"),
    )
    file_size = models.PositiveIntegerField(
        verbose_name=_("File size (bytes)"),
    )
    direction = models.CharField(
        max_length=20,
        verbose_name=_("Translation direction"),
    )

    # Translation result metadata
    characters = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Characters translated"),
    )
    api_calls = models.PositiveIntegerField(
        default=0,
        verbose_name=_("API calls"),
    )
    duration_seconds = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Translation duration (seconds)"),
    )
    output_filename = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Output filename"),
    )

    # Disk path (relative to MEDIA_ROOT)
    result_path = models.CharField(
        max_length=512,
        blank=True,
        default="",
        verbose_name=_("Result file path"),
    )
    downloaded = models.BooleanField(
        default=False,
        verbose_name=_("Downloaded"),
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Download count"),
    )

    # Set to True for .docx jobs that contained at least one user footnote or
    # endnote, so the UI can warn the user to verify footnote positions.
    has_footnotes = models.BooleanField(
        default=False,
        verbose_name=_("Has footnotes or endnotes"),
        help_text=_(
            "True when the translated Word document contained footnotes or "
            "endnotes.  Always False for PowerPoint jobs."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Document Translation Job")
        verbose_name_plural = _("Document Translation Jobs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session_key", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
