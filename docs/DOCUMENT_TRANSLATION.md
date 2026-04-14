<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Document Translation (Beta)

The document translation feature allows users to upload Word (`.docx`) or PowerPoint (`.pptx`) files and receive a translated version with the original formatting and structure preserved.

> **Note:** This feature is currently in **Beta**. The tab heading in the UI displays a "beta" badge.

## Enabling the Feature

Set the following in your environment file (`env/deepl.env`):

```bash
DOCUMENT_TRANSLATION_ENABLED=True
```

When disabled (the default), the translation page shows only the text translation form. When enabled, a tabbed interface appears with **Text Translation** and **Document Translation (Beta)** tabs.

## How It Works

1. The user selects a translation direction (e.g., German → English) and uploads a `.docx` or `.pptx` file.
2. The upload is submitted via AJAX; the server creates a `DocumentTranslationJob` record and saves the file to `MEDIA_ROOT/doc_translations/<job-uuid>/`.
3. A **background thread** translates the document paragraph-by-paragraph via the DeepL API.
4. The browser **polls** the job status endpoint (`/translation/document/<id>/status/`) every 1.5 seconds, showing a spinner and progress indicator.
5. Once complete, a result card displays metadata (filename, size, characters, duration) and a **Download** button.
6. The user clicks the button to download the file. Files remain available until the **10-minute cleanup** removes them. On page reload, a completed-but-not-yet-downloaded job resumes directly to the download page.
7. Only **one active job per session** is allowed. Uploading a new document while one is pending or processing is rejected with a 409 error.

### Async Architecture

| Endpoint | Method | Purpose |
|---|---|---|
| `/translation/document/` | POST | Accept upload, create job, start background thread |
| `/translation/document/<id>/status/` | GET | Poll job status (JSON) |
| `/translation/document/<id>/download/` | GET | Serve translated file |

All endpoints enforce **session-based access control**: only the session that created a job can poll its status or download the result.

### File Lifecycle & Cleanup

- Translated files are stored on disk at `MEDIA_ROOT/doc_translations/<job-uuid>/`.
- Files are **not** deleted on download — users can re-download within the cleanup window.
- **On failure** (API error, timeout, character-limit exceeded, missing library), the uploaded file is deleted from disk **immediately** to avoid leaving sensitive content on the server.
- A **lazy cleanup** runs every time the main translation form is loaded: jobs older than **10 minutes** (regardless of status) have their files deleted from disk and their `result_path` cleared.
- The `DocumentTranslationJob` database records are retained for auditing (only the files are removed).
- Uploaded filenames are sanitised (`os.path.basename`) to prevent path-traversal attacks.

### What Gets Translated

**Word documents (.docx):**
- Body paragraphs
- Table cell contents
- Headers and footers

**PowerPoint presentations (.pptx):**
- Text frames on all slides
- Table cell contents
- Grouped shapes (recursively)
- Slide notes

### What Is Preserved

- Document structure (headings, lists, tables, slide layouts)
- Paragraph-level formatting (alignment, indentation, spacing)
- The first run's character formatting (font, size, bold, italic, colour) is applied to the translated text
- Images, charts, and other embedded objects
- Page/slide layout and margins

## Translation Strategy

Text is translated **per paragraph**.  All runs (the smallest unit of
consistently formatted text in Office documents) within a paragraph are
concatenated into a single string, translated as one unit, and the result
is placed into the first run while the remaining runs are emptied.

Why not translate per run?

- Word (and PowerPoint) frequently splits visually identical text across
  many runs due to **editing-history tracking** (`rsid` attributes),
  spell-check state, revision markers, and other internal bookkeeping.
  A sentence that *looks* uniformly formatted may be stored as 5+ runs.
- Translating each tiny fragment independently produces **poor translation
  quality** because the API lacks sentence context.
- Spaces at run boundaries are often stripped by the API, causing
  **words to merge** in the translated output.

The paragraph-level strategy:

- **Gives the translator full sentence context** for higher quality results.
- **Eliminates whitespace loss** at run boundaries.
- **Reduces API calls** significantly (one per paragraph instead of one per run).

The trade-off is that mixed character formatting *within* a single
paragraph (e.g. one bold word in an otherwise regular sentence) is
replaced by the formatting of the first run.  In practice this is rarely
noticeable because most run splits are invisible artefacts of Word's
editing history, not intentional formatting differences.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DOCUMENT_TRANSLATION_ENABLED` | `False` | Enable the document translation tab |
| `DOCUMENT_TRANSLATION_TIMEOUT` | `180` | Maximum wall-clock seconds for a single document translation (0 = unlimited) |
| `MAX_TRANSLATION_LENGTH` | `0` | Maximum characters allowed per document (0 = unlimited).  Before translation begins a pre-flight check counts the characters in the uploaded document; if the count exceeds this limit the job fails immediately. |

## Limitations

- Maximum file size: **50 MB**
- Only `.docx` and `.pptx` formats are supported (not `.doc`, `.ppt`, `.pdf`, etc.)
- Mixed character formatting within a single paragraph is not preserved (see *Translation Strategy* above).
- The feature requires `python-docx` and `python-pptx` libraries (included in `requirements.txt`).
- Translated files are stored on disk temporarily (up to 10 minutes); only the character count, direction, and job metadata are persisted in the database.
- Auto-detection of the source language is not available for document translation; the user must select the direction explicitly.
- Translation runs in a background thread using Python's `threading` module; there is no external task queue (e.g. Celery). This is suitable for low-to-moderate concurrency.

## Dependencies

The following Python packages are required (already listed in `requirements.txt`):

```
python-docx~=1.1.0
python-pptx~=1.0.0
```

These are installed automatically when building the Docker image.

## Troubleshooting

### "Document translation is not enabled"
Set `DOCUMENT_TRANSLATION_ENABLED=True` in your environment file and restart the application.

### Translation takes a long time
Large documents with many paragraphs each require an API call. Consider splitting very large documents. You can also configure `DOCUMENT_TRANSLATION_TIMEOUT` to abort long-running translations (default: 180 seconds).

### Formatting looks different after translation
The translation replaces the text content of each paragraph.  If the translated text is significantly longer or shorter than the original, minor layout shifts may occur (e.g., text wrapping differently in table cells).  Mixed character formatting within a single paragraph (e.g. one bold word) will be replaced by the formatting of the first run; this is a known trade-off of the paragraph-level translation strategy.

### "A required library is not installed"
Ensure `python-docx` and `python-pptx` are installed. In Docker, rebuild the image:
```bash
docker-compose build deepl
```

### Error processing the document
Ensure the uploaded file is a valid, uncorrupted `.docx` or `.pptx` file. Password-protected or DRM-restricted documents cannot be processed.
