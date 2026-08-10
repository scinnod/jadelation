# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Django management command to remove a glossary from the local database
and optionally from the DeepL API.

Default behaviour is LOCAL-ONLY removal: the local DB record is deleted
and the glossary returns to UNTRACKED state in DeepL.  This is safe
because the glossary continues to exist in DeepL and can be re-imported
at any time via 'glossary_list --import'.

To also remove the glossary from the DeepL API, either:
  - Answer 'y' to the interactive prompt (only shown when not orphaned), or
  - Pass --also-remove-online explicitly (combined with --force for scripts).

Usage:
    python manage.py glossary_remove <name_or_id>
    python manage.py glossary_remove <name_or_id> --force
    python manage.py glossary_remove <name_or_id> --force --also-remove-online

Examples:
    python manage.py glossary_remove "AWI DE->EN"
    python manage.py glossary_remove 3f056e0e-dcbc-4fed-a983-382015eae522 --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import deepl

from deeplFrontend.models import Glossary


class Command(BaseCommand):
    help = (
        "Remove a glossary from the local database (default: keeps DeepL copy). "
        "Use --also-remove-online to also delete from the DeepL API."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Glossary name or DeepL glossary ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--also-remove-online',
            action='store_true',
            dest='also_remove_online',
            help='Also delete the glossary from the DeepL API',
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        force = options['force']
        also_remove_online = options['also_remove_online']

        # Find glossary by ID first, then by name
        try:
            glossary = Glossary.objects.get(glossary_id=identifier)
        except Glossary.DoesNotExist:
            try:
                glossary = Glossary.objects.get(name=identifier)
            except Glossary.DoesNotExist:
                raise CommandError(
                    f"Glossary not found with name or ID: '{identifier}'\n"
                    "Use 'python manage.py glossary_list' to see available glossaries."
                )
            except Glossary.MultipleObjectsReturned:
                matches = Glossary.objects.filter(name=identifier)
                self.stderr.write(
                    self.style.ERROR(
                        f"Multiple glossaries found with name '{identifier}':\n"
                    )
                )
                for g in matches:
                    self.stdout.write(
                        f"  - {g.name} (ID: {g.glossary_id}, "
                        f"{g.source_lang}->{g.target_lang})"
                    )
                raise CommandError(
                    "Please use the glossary ID instead to specify which one to remove."
                )

        # Display glossary information
        self.stdout.write(
            f"\nGlossary to be removed:\n"
            f"  Name:      {glossary.name}\n"
            f"  ID:        {glossary.glossary_id}\n"
            f"  Languages: {glossary.source_lang} -> {glossary.target_lang}\n"
            f"  Entries:   {glossary.entry_count}\n"
            f"  Uploaded:  {glossary.upload_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Filename:  {glossary.original_filename}\n"
            f"  Comment:   {glossary.comment or '(none)'}\n"
        )

        # Confirm unless --force
        if not force:
            confirm = input(
                "\nRemove glossary from local database? [y/N]: "
            ).strip().lower()
            if confirm != 'y':
                self.stdout.write(
                    self.style.WARNING("Cancelled. Glossary was not removed.")
                )
                return

        # Decide whether to also remove from DeepL
        remove_online = also_remove_online
        translator = None   # initialised lazily when needed

        if not also_remove_online and not force:
            # Interactive path: check if glossary still exists in DeepL
            # and prompt the user — only when not orphaned.
            try:
                translator = deepl.Translator(settings.DEEPL_AUTHKEY)
                translator.get_glossary(glossary.glossary_id)
                # Glossary found in DeepL — offer to remove it too
                self.stdout.write(
                    "\nThis glossary still exists in the DeepL API.\n"
                    "Other applications using the same DeepL account may rely on it."
                )
                online_answer = input(
                    "Also remove from DeepL API? [y/N]: "
                ).strip().lower()
                remove_online = online_answer == 'y'
            except deepl.DeepLException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    # Orphaned — nothing to ask
                    pass
                else:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Could not check DeepL status: {e}. "
                            "Proceeding with local removal only."
                        )
                    )
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(
                        f"Could not check DeepL status: {e}. "
                        "Proceeding with local removal only."
                    )
                )

        # --- Remove from local database ---
        glossary_name = glossary.name
        try:
            glossary.delete()
        except Exception as e:
            raise CommandError(f"Database error: {e}")
        self.stdout.write(
            self.style.SUCCESS("✓ Glossary removed from local database")
        )

        # --- Remove from DeepL API (if requested) ---
        if remove_online:
            if translator is None:
                try:
                    translator = deepl.Translator(settings.DEEPL_AUTHKEY)
                except (AttributeError, ValueError) as e:
                    raise CommandError(f"DeepL configuration error: {e}")

            self.stdout.write("Removing glossary from DeepL API...")
            try:
                deepl_glossary = translator.get_glossary(glossary.glossary_id)
                translator.delete_glossary(deepl_glossary)
                self.stdout.write(
                    self.style.SUCCESS("✓ Glossary removed from DeepL API")
                )
            except deepl.DeepLException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠ Glossary not found in DeepL API "
                            "(may have been deleted already)"
                        )
                    )
                else:
                    raise CommandError(f"DeepL API error: {e}")
            except Exception as e:
                raise CommandError(
                    f"Unexpected error during DeepL deletion: {e}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Glossary '{glossary_name}' has been successfully removed!"
            )
        )

