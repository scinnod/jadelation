# SPDX-License-Identifier: Apache-2.0
"""
Django management command to list all glossaries.

Usage:
    python manage.py glossary_list [--verbose]

Example:
    python manage.py glossary_list
    python manage.py glossary_list --verbose
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import deepl

from deeplFrontend.models import Glossary


class Command(BaseCommand):
    help = "List all glossaries stored in the database with their metadata"

    def add_arguments(self, parser):
        """Define command line arguments."""
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each glossary'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Sync database with DeepL API (check for orphaned entries)'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        verbose = options['verbose']
        sync = options['sync']

        # Get all glossaries from database
        glossaries = Glossary.objects.all().order_by('-upload_date')

        if not glossaries:
            self.stdout.write(
                self.style.WARNING("No glossaries found in database.")
            )
            return

        # If sync option, check against DeepL API
        if sync:
            self.stdout.write("Syncing with DeepL API...")
            try:
                translator = deepl.Translator(settings.DEEPL_AUTHKEY)
                deepl_glossaries = translator.list_glossaries()
                deepl_ids = {g.glossary_id for g in deepl_glossaries}
                
                # Check for orphaned database entries
                for glossary in glossaries:
                    if glossary.glossary_id not in deepl_ids:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  WARNING: Glossary '{glossary.name}' (ID: {glossary.glossary_id}) "
                                f"exists in database but not in DeepL API"
                            )
                        )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Failed to sync with DeepL API: {e}")
                )

        # Display header
        count = glossaries.count()
        self.stdout.write(
            self.style.SUCCESS(f"\nFound {count} glossar{'ies' if count != 1 else 'y'}:\n")
        )

        # Display glossaries
        for i, glossary in enumerate(glossaries, 1):
            if verbose:
                # Detailed view
                self.stdout.write(
                    f"{i}. {self.style.SUCCESS(glossary.name)}\n"
                    f"   ID:        {glossary.glossary_id}\n"
                    f"   Languages: {glossary.source_lang} -> {glossary.target_lang}\n"
                    f"   Entries:   {glossary.entry_count}\n"
                    f"   Uploaded:  {glossary.upload_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   Filename:  {glossary.original_filename}\n"
                    f"   Comment:   {glossary.comment if glossary.comment else '(none)'}\n"
                )
            else:
                # Compact view
                days_ago = (timezone.now() - glossary.upload_date).days
                age_str = f"{days_ago}d ago" if days_ago > 0 else "today"
                
                self.stdout.write(
                    f"{i}. {self.style.SUCCESS(glossary.name):40s} "
                    f"[{glossary.language_pair:10s}] "
                    f"{glossary.entry_count:4d} entries  "
                    f"({age_str:10s})  "
                    f"ID: {glossary.glossary_id}"
                )

        # Display usage hint
        self.stdout.write(
            f"\n"
            f"Use 'python manage.py glossary_list --verbose' for detailed information.\n"
            f"Use 'python manage.py glossary_remove <name_or_id>' to delete a glossary.\n"
        )
