# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Django management command to promote a glossary to ACTIVE status.

Touches the upload_date of the specified glossary to the current time,
making it the most recently uploaded entry for its language pair.  The
_GlossaryCache will then select it as the ACTIVE glossary for that pair
on the next cache refresh.

Use this to:
  - Promote a SHADOWED glossary without deleting and re-uploading it.
  - Revert an unwanted promotion: run glossary_activate on the glossary
    you actually want to be active.

The command verifies that the glossary exists in the DeepL API before
making any change.  It will refuse to activate an ORPHANED glossary
(one that is in the local DB but absent from DeepL) because the app
cannot load it.

Usage:
    python manage.py glossary_activate <name_or_id>

Examples:
    python manage.py glossary_activate "AWI DE->EN 2024"
    python manage.py glossary_activate 3f056e0e-dcbc-4fed-a983-382015eae522
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import deepl

from deeplFrontend.models import Glossary


class Command(BaseCommand):
    help = (
        "Promote a SHADOWED glossary to ACTIVE by touching its upload_date. "
        "Verifies the glossary exists in the DeepL API first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Glossary name or DeepL glossary ID',
        )

    def handle(self, *args, **options):
        identifier = options['identifier']

        # Find glossary in local DB
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
                    "Please use the glossary ID instead to specify which one to activate."
                )

        # Verify glossary still exists in DeepL (not ORPHANED)
        self.stdout.write("Verifying glossary in DeepL API...")
        try:
            translator = deepl.Translator(settings.DEEPL_AUTHKEY)
            translator.get_glossary(glossary.glossary_id)
        except deepl.DeepLException as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.stderr.write(
                    self.style.ERROR(
                        f"Glossary '{glossary.name}' is ORPHANED "
                        "(not found in DeepL API).\n"
                        "The app cannot use an ORPHANED glossary. "
                        "Run 'glossary_remove' to clean it up."
                    )
                )
                raise SystemExit(1)
            raise CommandError(f"DeepL API error: {e}")
        except (AttributeError, ValueError) as e:
            raise CommandError(f"DeepL configuration error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error checking DeepL: {e}")

        # Determine the normalised language pair key
        norm_key = (
            f"{glossary.source_lang[:2].upper()}"
            f"->"
            f"{glossary.target_lang[:2].upper()}"
        )

        # Find all DB entries for this pair, newest first (same logic as _GlossaryCache)
        all_for_pair = [
            g for g in Glossary.objects.all().order_by("-upload_date")
            if (
                f"{g.source_lang[:2].upper()}->{g.target_lang[:2].upper()}"
                == norm_key
            )
        ]

        # Check if already ACTIVE
        if all_for_pair and all_for_pair[0].pk == glossary.pk:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Glossary '{glossary.name}' is already ACTIVE for "
                    f"{norm_key}. No change needed."
                )
            )
            return

        # Touch upload_date → this entry becomes the newest for its pair
        Glossary.objects.filter(pk=glossary.pk).update(
            upload_date=timezone.now()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n\u2713 Glossary '{glossary.name}' is now ACTIVE for {norm_key}.\n"
                "  The application cache will pick it up within "
                "GLOSSARY_CACHE_TTL seconds."
            )
        )

        # Show what is now SHADOWED (if anything)
        shadowed = [g for g in all_for_pair if g.pk != glossary.pk]
        for s in shadowed:
            self.stdout.write(
                self.style.WARNING(
                    f"  SHADOWED: '{s.name}' ({s.source_lang}->{s.target_lang})"
                )
            )
