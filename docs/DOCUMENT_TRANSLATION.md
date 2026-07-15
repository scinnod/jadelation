<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Document Translation

The document translation feature allows users to upload Word (`.docx`) or PowerPoint (`.pptx`) files and receive a translated version with the original formatting and structure preserved.

## Enabling the Feature

Set the following in your environment file (`env/deepl.env`):

```bash
DOCUMENT_TRANSLATION_ENABLED=True
```

When disabled (the default), the translation page shows only the text translation form. When enabled, a tabbed interface appears with **Text Translation** and **Document Translation** tabs.

### Email-Based Access Control

Instead of enabling document translation for everyone, you can restrict access
to users whose email address matches a regular expression.  The email is read
from the `X-Remote-Email` HTTP header, which is set by
[oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) after
authentication via Keycloak (or another OIDC provider).

Set `DOCUMENT_TRANSLATION_ENABLED` to any string that is not `True`, `False`,
`true`, `false`, `1`, `0`, `yes`, or `no` and it is treated as a
case-insensitive regular expression:

```bash
# All @university.org addresses
DOCUMENT_TRANSLATION_ENABLED=@university\.org$

# @university.org PLUS two specific individuals
DOCUMENT_TRANSLATION_ENABLED=@university\.org$|^john\.doe@email\.test$|^anotherone@somemail\.example$

# Everyone (any valid email address contains @)
DOCUMENT_TRANSLATION_ENABLED=@
```

**How it works:**

1. On every request `DocumentTranslationsMiddleware` reads `X-Remote-Email`.
2. If the email matches the regex, `request.session['document_translations']`
   is set to `True`.
3. If the email does *not* match, the session flag is removed.
4. Views and the context processor read the session flag to decide whether to
   show the document translation tab or accept document uploads.

**Security note:** The `X-Remote-Email` header is set by oauth2-proxy *after*
authentication and must not be trusted when the application is accessed
directly (not through the nginx/oauth2-proxy stack).  The middleware only
grants access — it does not perform authentication itself.

## Fair Use Confirmation

Before uploading, users must tick a **confirmation checkbox** affirming that the translation is needed for an acceptable purpose (e.g. study, teaching, research, or administration). Below the checkbox a note reminds users that translation costs are charged per document and that the service should be used responsibly.

The checkbox is:

- **Unchecked by default** on every page load and after each "Translate another document" reset.
- **Required** – the submit button remains disabled until it is checked (enforced client-side via JavaScript, and server-side via a required `BooleanField` validated by Django).

This is a soft awareness measure, not an access restriction.  Its purpose is to encourage responsible use and to make users conscious that each document translation incurs costs.

### Disabling the fair-use checkbox

If no confirmation is required (e.g. for an internal-only deployment where all users are authorised), the checkbox can be suppressed by setting **all** language variants to the literal string `False` (any capitalisation) in the env file:

```bash
DOCUMENT_TRANSLATION_FAIR_USE_TEXT_EN=False
DOCUMENT_TRANSLATION_FAIR_USE_TEXT_DE=False
```

When all language variants are cleared the checkbox disappears from the upload form and the backend receives an automatic confirmation via a hidden input (`<input type="hidden" name="fair_use_confirmed" value="on">`).  Django's `BooleanField(required=True)` accepts this value as `True`, so no backend changes are needed and no new security surface is introduced.

> **Note:** Empty-string values (`DOCUMENT_TRANSLATION_FAIR_USE_TEXT_EN=`) are **not** treated as a disable signal — only the literal string `False` (any capitalisation) removes a language variant.  You must clear **every** configured language (default: `EN` and `DE`) to suppress the checkbox entirely; leaving any language set means the fallback chain in the context processor will still find a non-empty text and show the checkbox.

### Access Notice Banner

When `DOCUMENT_TRANSLATION_ENABLED` is set to a **regex string**, an informational
banner is automatically shown **only to users who have access** (i.e. whose email
matched the regex).  The banner is never shown when the feature is globally
enabled (`True`) or disabled (`False`).

The banner text is language-aware and uses the same `_<LANG>` suffix convention
as other branding settings.  Built-in defaults are provided so no configuration
is needed for a typical regex-mode deployment:

| Language | Default text |
|---|---|
| EN | *Document translation may not be available to all users.* |
| DE | *Die Dokumentübersetzung ist möglicherweise nicht für alle Nutzer verfügbar.* |

To **customise** the text, set the env vars in `env/deepl.env`:

```bash
DOCUMENT_TRANSLATION_NOTICE_EN=Document translation is currently in a restricted pilot phase.
DOCUMENT_TRANSLATION_NOTICE_DE=Die Dokumentübersetzung befindet sich derzeit in einer eingeschränkten Pilotphase.
```

To **suppress** the banner entirely even in regex mode, set all language
variants to the literal string `False` (any capitalisation):

```bash
DOCUMENT_TRANSLATION_NOTICE_EN=False
DOCUMENT_TRANSLATION_NOTICE_DE=False
```

The same `False` sentinel works for all `_collect_i18n_env`-backed settings:
it removes the built-in default for that language, and when every language is
cleared the resulting dict is empty, which the context processor treats as "no
text configured".

### Customising the checkbox text

The label of the confirmation checkbox is read from the environment at startup and can be tailored to your organisation's acceptable-use policy.  Set one variable per supported language using the `_<LANG>` suffix convention (uppercase ISO 639-1 code):

```bash
# env/deepl.env
DOCUMENT_TRANSLATION_FAIR_USE_TEXT_EN=I confirm that I need this translation for a purpose in the context of study, teaching, research, or administration at Example University.
DOCUMENT_TRANSLATION_FAIR_USE_TEXT_DE=Ich bestätige, dass ich diese Übersetzung für einen Zweck im Kontext von Studium, Lehre, Forschung oder Verwaltung an der Beispiel Universität benötige.
```

When these variables are not set, the application uses generic fallback texts that do not mention a specific institution.

> **Security note:** The checkbox is a `BooleanField(required=True)` in `DocumentTranslationForm`.  Django's form validation raises a `ValidationError` when the field is missing or `False`, so the server-side check is independent of the client-side JavaScript.

## File picker pre-filtering

The document upload field sets the HTML `accept` attribute to `.docx`, `.pptx`, and their corresponding MIME types.  The OS file dialog therefore defaults to showing only Word and PowerPoint files.  Users can switch to "All files" at any time — any file type that is not `.docx` or `.pptx` will be rejected by client-side JavaScript and server-side form validation independently.

File extension matching is **case-insensitive** throughout the stack: `.DOCX`, `.Docx`, `.pptx`, and `.PPTX` are all accepted by both the client-side validator and the server-side `clean_document` method.

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
| `DOCUMENT_TRANSLATION_ENABLED` | `False` | `True` – visible to all; `False` – hidden; regex string – visible only to users whose `X-Remote-Email` matches the pattern (case-insensitive) |
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

## Statistics Integration

Document translations are recorded in the same `Translation` database table as text translations, with the `is_document_translation` flag set to `True`.  This means they are included in the standard usage statistics (request count and character usage) without any separate tracking.

In addition, the statistics pages (`/stat/d`, `/stat/m`, `/stat/y`) display a **whereof documents** column showing, for each period, how many translations were document translations and what share of all translations they represent (e.g. `3 (25%)`).  This column is shown only to users who are eligible to use document translation — it is hidden for users without access or when the feature is globally disabled.

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

### "An unexpected error occurred" on upload / 413 Request Entity Too Large
The built-in nginx is configured with `client_max_body_size 55M`. If you have a **downstream reverse proxy** (e.g. Nginx Proxy Manager, Traefik, or another nginx instance), make sure it also allows request bodies of at least 55 MB. The default `client_max_body_size` in nginx is only 1 MB; uploads exceeding that limit will be rejected with a `413` error which surfaces in the UI as a generic "unexpected error" because the non-JSON error page cannot be parsed by the JavaScript client.

### Error processing the document
Ensure the uploaded file is a valid, uncorrupted `.docx` or `.pptx` file. Password-protected or DRM-restricted documents cannot be processed.
