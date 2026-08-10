# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Django management command to list all glossaries with their sync status.

Shows every glossary known to either the local database or the DeepL API,
classified into one of four states:

  ACTIVE    - in DB, in DeepL API, ready, newest for its language pair
              → the app WILL use this glossary for translations
  SHADOWED  - in DB, in DeepL API, but superseded by a newer upload for
              the same pair → the app will NOT use this one
  ORPHANED  - in DB, but absent from the DeepL API → broken reference;
              clean up with 'glossary_remove'
  UNTRACKED - in the DeepL API only, not in local DB → the app will
              NEVER use it; register with 'glossary_list --import'

The state logic mirrors _GlossaryCache._load() in views.py so the output
exactly reflects what the application does at runtime.

Usage:
    python manage.py glossary_list [--verbose] [--import]

Examples:
    python manage.py glossary_list
    python manage.py glossary_list --verbose
    python manage.py glossary_list --import

Exit codes:
    0 - all good (only ACTIVE and/or SHADOWED glossaries)
    1 - at least one ORPHANED or UNTRACKED glossary found
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import deepl

from deeplFrontend.models import Glossary

STATE_ACTIVE = "ACTIVE"
STATE_SHADOWED = "SHADOWED"
STATE_ORPHANED = "ORPHANED"
STATE_UNTRACKED = "UNTRACKED"


class Command(BaseCommand):
    help = (
        "List all glossaries (local DB and DeepL API) with their sync status. "
        "Exits with code 1 if any ORPHANED or UNTRACKED entries are found."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information for each glossary",
        )
        parser.add_argument(
            "--import",
            dest="do_import",
            action="store_true",
            help=(
                "Interactively prompt to import UNTRACKED glossaries "
                "(those in the DeepL API but not in the local database) "
                "into the local DB"
            ),
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]
        do_import = options["do_import"]

        # Initialise DeepL translator
        try:
            translator = deepl.Translator(settings.DEEPL_AUTHKEY)
        except (AttributeError, ValueError) as e:
            raise CommandError(f"DeepL configuration error: {e}")

        # Fetch all glossaries from DeepL API
        try:
            deepl_glossaries = translator.list_glossaries()
        except deepl.DeepLException as e:
            raise CommandError(f"DeepL API error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error fetching glossaries from DeepL: {e}")

        deepl_by_id = {g.glossary_id: g for g in deepl_glossaries}

        # Fetch all glossaries from local DB, newest first.
        # This ordering mirrors _GlossaryCache._load() so state detection
        # is faithful to actual runtime behaviour.
        db_glossaries = list(Glossary.objects.all().order_by("-upload_date"))
        db_ids = {g.glossary_id for g in db_glossaries}

        # Determine state for every DB entry using the same "newest-wins per
        # normalised pair" logic as _GlossaryCache._load().
        seen_pairs = set()
        db_states = {}

        for db_g in db_glossaries:
            norm_key = f"{db_g.source_lang[:2].upper()}->{db_g.target_lang[:2].upper()}"
            if db_g.glossary_id not in deepl_by_id:
                db_states[db_g.glossary_id] = STATE_ORPHANED
            elif norm_key in seen_pairs:
                db_states[db_g.glossary_id] = STATE_SHADOWED
            else:
                seen_pairs.add(norm_key)
                db_states[db_g.glossary_id] = STATE_ACTIVE

        # Identify UNTRACKED entries (in DeepL but absent from local DB)
        untracked = [g for g in deepl_glossaries if g.glossary_id not in db_ids]

        # ------------------------------------------------------------------
        # Output: DB glossaries
        # ------------------------------------------------------------------
        if db_glossaries:
            self.stdout.write(f"\nDB glossaries ({len(db_glossaries)}):\n")
            for i, db_g in enumerate(db_glossaries, 1):
                state = db_states[db_g.glossary_id]
                deepl_g = deepl_by_id.get(db_g.glossary_id)
                self._print_db_entry(i, db_g, state, deepl_g, verbose)
        else:
            self.stdout.write(self.style.WARNING("\nNo glossaries in local database.\n"))

        # ------------------------------------------------------------------
        # Output: UNTRACKED glossaries
        # ------------------------------------------------------------------
        if untracked:
            self.stdout.write(
                self.style.WARNING(
                    f"\nUNTRACKED glossaries in DeepL API ({len(untracked)}):\n"
                )
            )
            for g in untracked:
                self._print_untracked(g, verbose)
        else:
            self.stdout.write("\nNo UNTRACKED glossaries in DeepL API.\n")

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        n_active = sum(1 for s in db_states.values() if s == STATE_ACTIVE)
        n_shadowed = sum(1 for s in db_states.values() if s == STATE_SHADOWED)
        n_orphaned = sum(1 for s in db_states.values() if s == STATE_ORPHANED)
        n_untracked = len(untracked)

        self.stdout.write(
            f"\nSummary: {n_active} ACTIVE, {n_shadowed} SHADOWED, "
            f"{n_orphaned} ORPHANED, {n_untracked} UNTRACKED\n"
        )

        self.stdout.write(
            "Use 'glossary_put' to upload a new glossary.\n"
            "Use 'glossary_remove <name_or_id>' to delete a glossary.\n"
        )
        if untracked and not do_import:
            self.stdout.write(
                "Use 'glossary_list --import' to import UNTRACKED glossaries.\n"
            )

        if n_orphaned:
            self.stderr.write(
                self.style.ERROR(
                    f"  {n_orphaned} ORPHANED "
                    f"glossar{'ies' if n_orphaned != 1 else 'y'} found. "
                    "Run 'glossary_remove' to clean them up."
                )
            )
        if n_untracked and not do_import:
            self.stderr.write(
                self.style.WARNING(
                    f"  {n_untracked} UNTRACKED "
                    f"glossar{'ies' if n_untracked != 1 else 'y'} "
                    "found in DeepL API but not in local DB. "
                    "Run 'glossary_list --import' to track them."
                )
            )

        # ------------------------------------------------------------------
        # Interactive import of UNTRACKED glossaries
        # ------------------------------------------------------------------
        if do_import and untracked:
            self._interactive_import(untracked)

        # Exit non-zero when actionable problems remain
        if n_orphaned > 0 or n_untracked > 0:
            raise SystemExit(1)

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _state_label(self, state):
        """Return a colour-coded, fixed-width state label."""
        label = f"[{state:9s}]"
        if state == STATE_ACTIVE:
            return self.style.SUCCESS(label)
        if state == STATE_SHADOWED:
            return self.style.WARNING(label)
        if state == STATE_ORPHANED:
            return self.style.ERROR(label)
        return label

    def _print_db_entry(self, index, db_g, state, deepl_g, verbose):
        label = self._state_label(state)
        days_ago = (timezone.now() - db_g.upload_date).days
        age_str = f"{days_ago}d ago" if days_ago > 0 else "today"
        if verbose:
            ready_str = str(deepl_g.ready) if deepl_g else "N/A (not in DeepL)"
            deepl_entries = deepl_g.entry_count if deepl_g else "N/A"
            self.stdout.write(
                f"  {index:2d}. {label} {db_g.name}\n"
                f"          ID:       {db_g.glossary_id}\n"
                f"          Langs:    {db_g.source_lang} -> {db_g.target_lang}\n"
                f"          Entries:  {db_g.entry_count} (DB) / {deepl_entries} (DeepL)\n"
                f"          Ready:    {ready_str}\n"
                f"          Uploaded: {db_g.upload_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"          File:     {db_g.original_filename}\n"
                f"          Comment:  {db_g.comment or '(none)'}\n"
            )
        else:
            not_ready = " (NOT READY)" if deepl_g and not deepl_g.ready else ""
            self.stdout.write(
                f"  {index:2d}. {label} {db_g.name:<38s} "
                f"[{db_g.source_lang}->{db_g.target_lang}]  "
                f"{db_g.entry_count:4d} entries  "
                f"({age_str}){not_ready}"
            )

    def _print_untracked(self, g, verbose):
        if verbose:
            self.stdout.write(
                f"      [UNTRACKED] {g.name}\n"
                f"          ID:      {g.glossary_id}\n"
                f"          Langs:   {g.source_lang} -> {g.target_lang}\n"
                f"          Entries: {g.entry_count}\n"
                f"          Ready:   {g.ready}\n"
            )
        else:
            self.stdout.write(
                f"      [UNTRACKED] {g.name:<38s} "
                f"[{g.source_lang}->{g.target_lang}]  "
                f"{g.entry_count:4d} entries"
            )

    # ------------------------------------------------------------------
    # Interactive import
    # ------------------------------------------------------------------

    def _interactive_import(self, untracked):
        self.stdout.write("\nInteractive import of UNTRACKED glossaries:\n")
        imported = 0
        for g in untracked:
            self.stdout.write(
                f"\n  Name:     {g.name}\n"
                f"  ID:       {g.glossary_id}\n"
                f"  Langs:    {g.source_lang} -> {g.target_lang}\n"
                f"  Entries:  {g.entry_count}\n"
                f"  Ready:    {g.ready}\n"
            )
            try:
                answer = input("  Import into local database? [y/N/q]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.stdout.write("\nImport cancelled.")
                break

            if answer == "q":
                self.stdout.write("  Import cancelled.")
                break
            if answer != "y":
                self.stdout.write("  Skipped.")
                continue

            try:
                comment = input(
                    "  Add a comment (leave blank to skip): "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                comment = ""

            try:
                Glossary.objects.create(
                    glossary_id=g.glossary_id,
                    name=g.name,
                    source_lang=g.source_lang,
                    target_lang=g.target_lang,
                    original_filename="(imported from DeepL API)",
                    comment=comment,
                    entry_count=g.entry_count,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  \u2713 Imported '{g.name}' into local database."
                    )
                )
                imported += 1
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"  Failed to import '{g.name}': {e}")
                )

        if imported:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n\u2713 Imported {imported} "
                    f"glossar{'ies' if imported != 1 else 'y'} "
                    "into local database.\n"
                    "  The application cache will pick them up within "
                    "GLOSSARY_CACHE_TTL seconds."
                )
            )
