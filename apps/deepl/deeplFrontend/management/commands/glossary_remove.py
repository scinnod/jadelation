# SPDX-License-Identifier: Apache-2.0
"""
Django management command to remove a glossary from DeepL API and database.

Usage:
    python manage.py glossary_remove <name_or_id>

Example:
    python manage.py glossary_remove "AWI DE->EN"
    python manage.py glossary_remove 3f056e0e-dcbc-4fed-a983-382015eae522
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import deepl

from deeplFrontend.models import Glossary


class Command(BaseCommand):
    help = "Remove a glossary from DeepL API and database"

    def add_arguments(self, parser):
        """Define command line arguments."""
        parser.add_argument(
            'identifier',
            type=str,
            help='Glossary name or DeepL glossary ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        identifier = options['identifier']
        force = options['force']

        # Try to find glossary by ID first, then by name
        try:
            # Try as glossary_id
            glossary = Glossary.objects.get(glossary_id=identifier)
        except Glossary.DoesNotExist:
            try:
                # Try as name
                glossary = Glossary.objects.get(name=identifier)
            except Glossary.DoesNotExist:
                raise CommandError(
                    f"Glossary not found with name or ID: '{identifier}'\n"
                    f"Use 'python manage.py glossary_list' to see available glossaries."
                )
            except Glossary.MultipleObjectsReturned:
                glossaries = Glossary.objects.filter(name=identifier)
                self.stderr.write(
                    self.style.ERROR(
                        f"Multiple glossaries found with name '{identifier}':\n"
                    )
                )
                for g in glossaries:
                    self.stdout.write(
                        f"  - {g.name} (ID: {g.glossary_id}, "
                        f"{g.source_lang}->{g.target_lang})"
                    )
                raise CommandError(
                    "Please use the glossary ID instead to specify which one to remove."
                )

        # Display glossary information
        self.stdout.write(
            f"\n"
            f"Glossary to be removed:\n"
            f"  Name:      {glossary.name}\n"
            f"  ID:        {glossary.glossary_id}\n"
            f"  Languages: {glossary.source_lang} -> {glossary.target_lang}\n"
            f"  Entries:   {glossary.entry_count}\n"
            f"  Uploaded:  {glossary.upload_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Filename:  {glossary.original_filename}\n"
            f"  Comment:   {glossary.comment if glossary.comment else '(none)'}\n"
        )

        # Confirm deletion unless --force is used
        if not force:
            confirm = input("\nAre you sure you want to remove this glossary? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(
                    self.style.WARNING("Cancelled. Glossary was not removed.")
                )
                return

        # Initialize DeepL translator
        try:
            translator = deepl.Translator(settings.DEEPL_AUTHKEY)
        except (AttributeError, ValueError) as e:
            raise CommandError(f"DeepL configuration error: {e}")

        # Try to delete from DeepL API
        self.stdout.write("Removing glossary from DeepL API...")
        
        try:
            # First, try to get the glossary to confirm it exists
            deepl_glossary = translator.get_glossary(glossary.glossary_id)
            translator.delete_glossary(deepl_glossary)
            self.stdout.write(
                self.style.SUCCESS("✓ Glossary removed from DeepL API")
            )
            deepl_deleted = True
        except deepl.DeepLException as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ Glossary not found in DeepL API (may have been deleted already)"
                    )
                )
                deepl_deleted = False
            else:
                raise CommandError(f"DeepL API error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error during DeepL deletion: {e}")

        # Delete from database
        self.stdout.write("Removing glossary from database...")
        
        try:
            glossary.delete()
            self.stdout.write(
                self.style.SUCCESS("✓ Glossary removed from database")
            )
        except Exception as e:
            raise CommandError(f"Database error: {e}")

        # Success message
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Glossary '{glossary.name}' has been successfully removed!"
            )
        )
