# SPDX-License-Identifier: Apache-2.0
"""
Django management command to upload a glossary to DeepL API.

Usage:
    python manage.py glossary_put <csv_file> <name> <source_lang> <target_lang> [--comment "description"]

Example:
    python manage.py glossary_put glossary.csv "AWI DE->EN" DE EN-GB --comment "AWI terminology 2025"
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import deepl

from deeplFrontend.models import Glossary


class Command(BaseCommand):
    help = "Upload a glossary CSV file to DeepL and store metadata in the database"

    def add_arguments(self, parser):
        """Define command line arguments."""
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV glossary file'
        )
        parser.add_argument(
            'name',
            type=str,
            help='Human-readable name for the glossary (e.g., "AWI DE->EN")'
        )
        parser.add_argument(
            'source_lang',
            type=str,
            help='Source language code (e.g., DE, EN)'
        )
        parser.add_argument(
            'target_lang',
            type=str,
            help='Target language code (e.g., EN-GB, DE)'
        )
        parser.add_argument(
            '--comment',
            type=str,
            default='',
            help='Optional comment or description for the glossary'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        csv_file = options['csv_file']
        name = options['name']
        source_lang = options['source_lang']
        target_lang = options['target_lang']
        comment = options['comment']

        # Validate file exists
        if not os.path.exists(csv_file):
            raise CommandError(f"CSV file not found: {csv_file}")

        # Validate file is readable
        if not os.path.isfile(csv_file):
            raise CommandError(f"Path is not a file: {csv_file}")

        # Get original filename
        original_filename = os.path.basename(csv_file)

        self.stdout.write(f"Reading CSV file: {csv_file}")

        # Read CSV file
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_data = f.read()
        except Exception as e:
            raise CommandError(f"Failed to read CSV file: {e}")

        # Validate CSV data
        if not csv_data.strip():
            raise CommandError("CSV file is empty")

        # Initialize DeepL translator
        try:
            translator = deepl.Translator(settings.DEEPL_AUTHKEY)
        except (AttributeError, ValueError) as e:
            raise CommandError(f"DeepL configuration error: {e}")

        # Upload glossary to DeepL
        self.stdout.write(
            f"Uploading glossary to DeepL API: {name} ({source_lang}->{target_lang})"
        )

        try:
            deepl_glossary = translator.create_glossary_from_csv(
                name=name,
                source_lang=source_lang,
                target_lang=target_lang,
                csv_data=csv_data
            )
        except deepl.DeepLException as e:
            raise CommandError(f"DeepL API error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error during glossary upload: {e}")

        # Store glossary metadata in database
        self.stdout.write("Storing glossary metadata in database...")

        try:
            glossary = Glossary.objects.create(
                glossary_id=deepl_glossary.glossary_id,
                name=name,
                source_lang=source_lang,
                target_lang=target_lang,
                original_filename=original_filename,
                comment=comment,
                entry_count=deepl_glossary.entry_count
            )
        except Exception as e:
            # If database save fails, try to delete the glossary from DeepL
            self.stderr.write(
                self.style.WARNING(
                    f"Failed to save glossary to database: {e}"
                )
            )
            self.stdout.write("Attempting to clean up DeepL glossary...")
            try:
                translator.delete_glossary(deepl_glossary)
                self.stdout.write(
                    self.style.WARNING("DeepL glossary deleted due to database error")
                )
            except Exception as cleanup_error:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to clean up DeepL glossary: {cleanup_error}. "
                        f"Manual cleanup required for glossary ID: {deepl_glossary.glossary_id}"
                    )
                )
            raise CommandError(f"Database error: {e}")

        # Success message
        self.stdout.write(
            self.style.SUCCESS(
                f"\n"
                f"✓ Glossary uploaded successfully!\n"
                f"  ID: {glossary.glossary_id}\n"
                f"  Name: {glossary.name}\n"
                f"  Languages: {glossary.source_lang} -> {glossary.target_lang}\n"
                f"  Entries: {glossary.entry_count}\n"
                f"  File: {glossary.original_filename}\n"
                f"  Upload Date: {glossary.upload_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  Comment: {glossary.comment if glossary.comment else '(none)'}"
            )
        )
