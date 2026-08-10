<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# DeepL Glossary Management

This document describes how to manage DeepL glossaries using Django management commands.

## Overview

Glossaries allow you to customize DeepL translations with domain-specific terminology. The system provides four management commands to handle glossary operations:

- `glossary_put` - Upload a new glossary
- `glossary_list` - List all glossaries with full sync status (ACTIVE / SHADOWED / ORPHANED / UNTRACKED)
- `glossary_activate` - Promote a SHADOWED glossary to ACTIVE without re-uploading
- `glossary_remove` - Remove a glossary from the local database (optionally also from DeepL)

All glossaries are stored both in the DeepL API and in the local database for tracking purposes.

## Prerequisites

1. Valid DeepL API authentication key configured in settings
2. CSV file formatted according to DeepL glossary specifications (source term, target term per line)
3. Database migrations applied: `python manage.py migrate`

## Commands

### 1. Upload a Glossary (glossary_put)

Upload a CSV glossary file to DeepL and store its metadata in the database.

**Syntax:**
```bash
python manage.py glossary_put <csv_file> <name> <source_lang> <target_lang> [--comment "description"]
```

**Arguments:**
- `csv_file`: Path to the CSV file containing glossary entries
- `name`: Human-readable name for the glossary (e.g., "AWI DE->EN")
- `source_lang`: Source language code (e.g., DE, EN)
- `target_lang`: Target language code (e.g., EN-GB, DE)
- `--comment`: (Optional) Description or notes about the glossary

**Examples:**
```bash
# Upload a German to English glossary
python manage.py glossary_put glossary_de_en.csv "AWI DE->EN" DE EN-GB --comment "AWI terminology 2025"

# Upload an English to German glossary
python manage.py glossary_put terms.csv "Technical Terms EN->DE" EN DE --comment "Technical documentation terms"
```

**CSV Format:**
```csv
source_term,target_term
Forschung,research
Wissenschaft,science
```

**Notes:**
- If database storage fails, the command automatically attempts to delete the glossary from DeepL to maintain consistency
- The glossary takes effect in the running application after the cache refreshes (within `GLOSSARY_CACHE_TTL` seconds, default 1 hour); no restart needed

### 2. List Glossaries with Status (glossary_list)

List every glossary known to either the local database or the DeepL API,
classified into one of four states:

| State | Meaning |
|-------|---------|
| **ACTIVE** | In DB, present in DeepL API, newest for its language pair → **will be used** |
| **SHADOWED** | In DB and DeepL API, but superseded by a newer upload for the same pair → won't be used |
| **ORPHANED** | In DB, but absent from DeepL API → broken; clean up with `glossary_remove` |
| **UNTRACKED** | In DeepL API only, not in local DB → the app will **never** use it |

The state logic mirrors the runtime `_GlossaryCache` exactly, so the output
reflects what the application will actually do at translation time.

**Syntax:**
```bash
python manage.py glossary_list [--verbose] [--import]
```

**Options:**
- `--verbose`: Show detailed information (ready flag, entry counts, upload date, comment)
- `--import`: Interactively prompt to import UNTRACKED glossaries into the local DB

**Exit codes:**
- `0` — all good (only ACTIVE and/or SHADOWED glossaries)
- `1` — at least one ORPHANED or UNTRACKED glossary found (suitable for monitoring/CI)

**Examples:**
```bash
# Standard list and status check
python manage.py glossary_list

# Detailed output
python manage.py glossary_list --verbose

# Discover and optionally import DeepL-side glossaries not yet tracked locally
python manage.py glossary_list --import
```

**Sample Output (compact):**
```
DB glossaries (2):

   1. [ACTIVE   ] AWI DE->EN                           [DE->EN-GB]   150 entries  (5d ago)
   2. [ACTIVE   ] Technical Terms EN->DE               [EN->DE   ]    85 entries  (12d ago)

No UNTRACKED glossaries in DeepL API.

Summary: 2 ACTIVE, 0 SHADOWED, 0 ORPHANED, 0 UNTRACKED
```

**Sample Output (verbose):**
```
DB glossaries (1):

   1. [ACTIVE   ] AWI DE->EN
          ID:       3f056e0e-dcbc-4fed-a983-382015eae522
          Langs:    DE -> EN-GB
          Entries:  150 (DB) / 150 (DeepL)
          Ready:    True
          Uploaded: 2025-12-14 10:30:45
          File:     glossary_de_en.csv
          Comment:  AWI terminology 2025
```

**Interactive import (`--import`):**

For each UNTRACKED glossary the command prompts:
```
  Name:     Remote Glossary
  ID:       3f056e0e-...
  Langs:    EN -> DE
  Entries:  85
  Ready:    True

  Import into local database? [y/N/q]: y
  Add a comment (leave blank to skip): Imported from DeepL, created by team X
  ✓ Imported 'Remote Glossary' into local database.
```

The `original_filename` field is set to `(imported from DeepL API)` since the
original CSV file is not retrievable from the DeepL API.

### 3. Activate a Glossary (glossary_activate)

Promote a SHADOWED glossary to ACTIVE by touching its `upload_date` to the
current time.  The application cache will then select it as the ACTIVE glossary
for its language pair on the next refresh.

Use this to:
- Deliberately switch between two local copies of a glossary for the same pair
- Revert an accidental promotion caused by importing an UNTRACKED entry

The command verifies the glossary still exists in the DeepL API before making
any change (it will refuse to activate an ORPHANED glossary).

**Syntax:**
```bash
python manage.py glossary_activate <name_or_id>
```

**Examples:**
```bash
python manage.py glossary_activate "AWI DE->EN 2024"
python manage.py glossary_activate 3f056e0e-dcbc-4fed-a983-382015eae522
```

**Exit codes:**
- `0` — glossary is now ACTIVE (or was already ACTIVE)
- `1` — glossary is ORPHANED (not found in DeepL API)

### 4. Remove a Glossary (glossary_remove)

Remove a glossary from the **local database** (default) and optionally also
from the DeepL API.

**Default behaviour is local-only removal.**  The glossary is untracked locally
but remains in the DeepL API; it returns to UNTRACKED state and can be
re-imported via `glossary_list --import` at any time.  This is the safest
default because other applications sharing the same DeepL account may rely on
the glossary.

**Syntax:**
```bash
python manage.py glossary_remove <name_or_id> [--force] [--also-remove-online]
```

**Arguments:**
- `name_or_id`: Glossary name or DeepL glossary ID
- `--force`: Skip confirmation prompt (still local-only by default)
- `--also-remove-online`: Also delete the glossary from the DeepL API

**Examples:**
```bash
# Remove from local DB only (interactive confirmation)
python manage.py glossary_remove "AWI DE->EN"

# Remove from local DB only, no prompt (for scripts / CI)
python manage.py glossary_remove "Old Glossary" --force

# Remove from local DB AND DeepL API, no prompt
python manage.py glossary_remove "Old Glossary" --force --also-remove-online
```

**Interactive flow (without --force):**
```
Glossary to be removed:
  Name:      AWI DE->EN
  ...

Remove glossary from local database? [y/N]: y

This glossary still exists in the DeepL API.
Other applications using the same DeepL account may rely on it.
Also remove from DeepL API? [y/N]: n

✓ Glossary removed from local database
✓ Glossary 'AWI DE->EN' has been successfully removed!
```

**Notes:**
- If the glossary is ORPHANED (not in DeepL), no DeepL prompt is shown
- If multiple glossaries share the same name, use the glossary ID

## How Glossaries Are Used

Glossaries are loaded **lazily** on the first translation request, not at
application startup.  The `_GlossaryCache` singleton in `views.py` reads all
`Glossary` records from the database (ordered by upload date, newest first),
fetches each `GlossaryInfo` from the DeepL API, and stores them in an
in-memory dict keyed by normalised 2-letter language codes (e.g. `DE->EN`).

The cache **auto-refreshes** after a configurable TTL (default: 1 hour / 3600 seconds,
configurable via `GLOSSARY_CACHE_TTL` in seconds in `settings.py` or the
`GLOSSARY_CACHE_TTL` environment variable).

### Language-code normalisation

Both the cache keys and the translation-view lookup normalise language codes
to their 2-letter base form.  This means a glossary uploaded with
`target_lang="EN-GB"` is stored under the key `DE->EN` and will match any
translation direction whose base codes are DE and EN.

### Duplicate language pairs

If **multiple glossaries** for the same language pair exist in the database,
only the **most recently uploaded** one is used — older duplicates for that
pair are skipped.  A log message is emitted for every skipped duplicate.

This means you can safely upload a new version of a glossary without first
removing the old one.  The new glossary will take effect automatically after
the cache refreshes (within `GLOSSARY_CACHE_TTL` seconds) or after a
container restart.

## Database Schema

The `Glossary` model stores:
- `glossary_id`: DeepL API glossary ID (unique)
- `name`: Human-readable name
- `source_lang`: Source language code
- `target_lang`: Target language code
- `upload_date`: Timestamp of upload
- `original_filename`: Original CSV filename
- `comment`: Optional description
- `entry_count`: Number of entries in the glossary

## Troubleshooting

### Glossary not being used in translations
1. Check that the glossary is ACTIVE: `python manage.py glossary_list`
   If it is SHADOWED, promote it with `python manage.py glossary_activate "<name>"`
2. Language codes are normalised to 2-letter base codes automatically;
   you do **not** need exact regional-variant matches
3. The cache refreshes automatically after the TTL expires (default 1 hour);
   restart the container to force an immediate reload
4. Check application logs for errors during glossary loading

### Wrong glossary became ACTIVE after an import
When a glossary is imported via `glossary_list --import`, its `upload_date` is
set to now, which may unintentionally shadow an existing active glossary.

To restore the intended state:
- Run `glossary_activate "<intended-name>"` to promote the correct glossary, **or**
- Run `glossary_remove "<imported-name>" --force` to un-track the import (it stays
  in DeepL and can be re-imported later)

### Upload fails with DeepL API error
- Verify CSV format matches DeepL specifications
- Check that source and target languages are valid DeepL language codes
- Ensure DeepL API key has glossary creation permissions
- Check DeepL API quota limits

### Glossaries out of sync between DB and DeepL API
Run `python manage.py glossary_list` for a full picture: it shows ACTIVE,
SHADOWED, ORPHANED, and UNTRACKED glossaries in one view and exits with code 1
if any action is needed.

For ORPHANED entries (in DB but absent from DeepL): remove them with `glossary_remove`.

For UNTRACKED entries (in DeepL but not in the local DB): the app will never use
them.  Run `python manage.py glossary_list --import` to register them locally.

## Best Practices

1. **Naming Convention**: Use descriptive names including language pair, e.g., "AWI DE->EN 2025"
2. **Comments**: Always add comments describing the glossary purpose and content
3. **Version Control**: Keep CSV files in version control for reproducibility
4. **Backup**: Regularly backup the database to preserve glossary metadata
5. **Testing**: Test glossaries with sample translations before deploying to production
6. **Monitoring**: Run `glossary_list` periodically (or in CI) to verify consistency; its exit code makes it easy to alert on problems

## Example Workflow

```bash
# 1. Prepare your glossary CSV file
cat > my_glossary.csv << EOF
Forschung,research
Wissenschaft,science
Entwicklung,development
EOF

# 2. Upload the glossary
python manage.py glossary_put my_glossary.csv "Research Terms DE->EN" DE EN-GB \
    --comment "Research terminology updated Dec 2025"

# 3. Verify upload
python manage.py glossary_list --verbose

# 4. Restart Django to load the new glossary
# (restart your Docker container or reload WSGI/ASGI)

# 5. Test translations (glossary will be automatically applied)

# 6. Later, when updating the glossary:
#    - Remove the old version
python manage.py glossary_remove "Research Terms DE->EN"

#    - Upload the new version
python manage.py glossary_put my_glossary_v2.csv "Research Terms DE->EN v2" DE EN-GB \
    --comment "Updated research terminology Jan 2026"
```
