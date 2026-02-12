<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# DeepL Glossary Management

This document describes how to manage DeepL glossaries using Django management commands.

## Overview

Glossaries allow you to customize DeepL translations with domain-specific terminology. The system provides three management commands to handle glossary operations:

- `glossary_put` - Upload a new glossary
- `glossary_list` - List all glossaries
- `glossary_remove` - Remove a glossary

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
- The glossary is immediately available for translations after upload (requires application restart to load)

### 2. List Glossaries (glossary_list)

Display all glossaries stored in the database with their metadata.

**Syntax:**
```bash
python manage.py glossary_list [--verbose] [--sync]
```

**Options:**
- `--verbose`: Show detailed information for each glossary
- `--sync`: Check DeepL API for orphaned entries (glossaries in DB but not in DeepL)

**Examples:**
```bash
# List all glossaries (compact view)
python manage.py glossary_list

# List with detailed information
python manage.py glossary_list --verbose

# List and check for sync issues
python manage.py glossary_list --sync
```

**Sample Output (compact):**
```
Found 2 glossaries:

1. AWI DE->EN                                [DE->EN-GB]     150 entries  (5d ago)      ID: 3f056e0e-dcbc-4fed-a983-382015eae522
2. Technical Terms EN->DE                    [EN->DE    ]     85 entries  (12d ago)     ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Sample Output (verbose):**
```
Found 2 glossaries:

1. AWI DE->EN
   ID:        3f056e0e-dcbc-4fed-a983-382015eae522
   Languages: DE -> EN-GB
   Entries:   150
   Uploaded:  2025-12-14 10:30:45
   Filename:  glossary_de_en.csv
   Comment:   AWI terminology 2025

2. Technical Terms EN->DE
   ID:        a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Languages: EN -> DE
   Entries:   85
   Uploaded:  2025-12-07 15:22:10
   Filename:  terms.csv
   Comment:   Technical documentation terms
```

### 3. Remove a Glossary (glossary_remove)

Remove a glossary from both DeepL API and the database.

**Syntax:**
```bash
python manage.py glossary_remove <name_or_id> [--force]
```

**Arguments:**
- `name_or_id`: Glossary name or DeepL glossary ID
- `--force`: Skip confirmation prompt (use with caution)

**Examples:**
```bash
# Remove by name (with confirmation prompt)
python manage.py glossary_remove "AWI DE->EN"

# Remove by ID (with confirmation prompt)
python manage.py glossary_remove 3f056e0e-dcbc-4fed-a983-382015eae522

# Remove without confirmation (for scripts)
python manage.py glossary_remove "Old Glossary" --force
```

**Sample Output:**
```
Glossary to be removed:
  Name:      AWI DE->EN
  ID:        3f056e0e-dcbc-4fed-a983-382015eae522
  Languages: DE -> EN-GB
  Entries:   150
  Uploaded:  2025-12-14 10:30:45
  Filename:  glossary_de_en.csv
  Comment:   AWI terminology 2025

Are you sure you want to remove this glossary? [y/N]: y

Removing glossary from DeepL API...
✓ Glossary removed from DeepL API
Removing glossary from database...
✓ Glossary removed from database

✓ Glossary 'AWI DE->EN' has been successfully removed!
```

**Notes:**
- If the glossary doesn't exist in DeepL API but exists in the database, it will only be removed from the database
- If multiple glossaries have the same name, use the glossary ID for removal

## How Glossaries Are Used

Once uploaded, glossaries are automatically loaded when the Django application starts. The `load_glossaries()` function in `views.py` reads all glossaries from the database and fetches their details from the DeepL API.

Glossaries are applied during translation based on the language pair:
- A translation from DE to EN-GB will use the glossary with key "DE->EN-GB" if available
- A translation from EN to DE will use the glossary with key "EN->DE" if available

**To reload glossaries without restarting the server:**
You need to restart the Django application (e.g., restart the Docker container or reload the WSGI/ASGI application).

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
1. Check that the glossary exists: `python manage.py glossary_list`
2. Verify the language pair matches exactly (DE->EN-GB vs DE->EN)
3. Restart the Django application to reload glossaries
4. Check application logs for errors during glossary loading

### Upload fails with DeepL API error
- Verify CSV format matches DeepL specifications
- Check that source and target languages are valid DeepL language codes
- Ensure DeepL API key has glossary creation permissions
- Check DeepL API quota limits

### Orphaned glossaries (in DB but not in DeepL)
Run `python manage.py glossary_list --sync` to identify orphaned entries, then remove them using `glossary_remove`.

## Best Practices

1. **Naming Convention**: Use descriptive names including language pair, e.g., "AWI DE->EN 2025"
2. **Comments**: Always add comments describing the glossary purpose and content
3. **Version Control**: Keep CSV files in version control for reproducibility
4. **Backup**: Regularly backup the database to preserve glossary metadata
5. **Testing**: Test glossaries with sample translations before deploying to production
6. **Monitoring**: Use `--sync` option periodically to check for consistency issues

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
