<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
-->

# Changelog

All notable changes to this project are documented here.

---

## [2.6] – August 2026

### Added
- `glossary_list` now classifies every known glossary as **ACTIVE**, **SHADOWED**, **ORPHANED**, or **UNTRACKED**, mirroring the runtime cache logic exactly
- `glossary_activate` command to promote a SHADOWED glossary without re-uploading
- `glossary_list --import` option to interactively import UNTRACKED (DeepL-side-only) glossaries into the local database

### Changed
- `glossary_remove` now removes from the local database only by default; pass `--also-remove-online` to also delete from the DeepL API
- Footer usage statistics simplified
- Added `<meta name="format-detection" content="telephone=no">` to prevent Apple/Safari telephone-number auto-detection

---

## [2.5] – July 2026

### Added
- Statistics view now includes document translation data per period (visible to eligible users only)

### Changed
- Document translation promoted from beta to production
- Statistics navigation improved (better period selection)
- Info panel moved from page header into the corresponding tab to reduce confusion
- Removed incidental Django framework references from HTML templates

### Fixed
- Footnotes and endnotes were silently dropped (and not translated) during document translation

---

## [2.4] – April 2026

### Added
- **Document translation** feature: translate entire `.docx` and `.pptx` files with in-place text replacement preserving document structure
- Configurable per-user access to document translation via regex match on `X-Remote-Email` header (`DOCUMENT_TRANSLATION_ENABLED`)
- Awareness / fair-use checkbox before document translation
- Info banner explaining document translation availability to eligible users
- JavaScript error handling and file-type validation on the upload form
- `MAX_TRANSLATION_LENGTH` setting to cap per-request API cost
- Configurable maximum document size (`MAX_DOCUMENT_SIZE_MB`, default 50 MB)

### Changed
- nginx `client_max_body_size` raised to accommodate document uploads
- Session lifetime extended to preserve beta tags across longer gaps
- Mobile logo display improved
- Header formatting and design updates

---

## [2.3] – February 2026

### Added
- Automated test suite with pytest covering models, forms, views, URLs, and template tags
- GitHub Actions CI workflow (Python 3.11 / 3.12 matrix)
- `pytest.ini`, `conftest.py`, `settings_test.py`, and `requirements-test.txt`
- `docs/TESTING.md` documentation

### Removed
- Completed pre-publication checklist (`docs/TODO.md`)
- Internal `LICENSE_INFO_COLLECTION.md`

---

## [2.2] – February 2026

### Added
- `overrides/` directory for organization-specific customization (logo, about texts)
- `docker-compose.override.yml.example` for transparent override mounting
- `overrides/README.md` explaining the customization mechanism

### Changed
- Documentation reorganized into `docs/` directory
- About page texts improved (clearer benefits, privacy information)

### Removed
- Direct `user_files/` volume mounts from `docker-compose.yml`

---

## [2.1] – January 2026

### Added
- Corporate identity customization: `PRIMARY_COLOR`, `SECONDARY_COLOR`, `LOGO_FILENAME` environment variables
- SSO logout button (optional; enabled via `SSO_LOGOUT_URL`)
- Authentication documentation for Django Auth Stack integration pattern
- SPDX license headers across source files

### Changed
- Docker container naming updated to current conventions
- Health check endpoint fixed

---

## [2.0] – December 2025

### Added
- Glossary management system with four Django management commands (`glossary_put`, `glossary_list`, `glossary_activate`, `glossary_remove`)
- Glossary caching with configurable TTL (`GLOSSARY_CACHE_TTL`)
- Environment-based configuration (no credentials in code)
- Comprehensive logging
- Local static assets (Bootstrap 5, jQuery) — no external CDN dependencies
- Responsive design with Bootstrap 5
- Configurable branding (`APP_TITLE_<LANG>`, `ORGANIZATION_NAME_<LANG>`, `FOOTER_TEXT`)
- Production-ready security settings (`DEBUG=False` by default, auto-generated `SECRET_KEY`)

### Changed
- Templates refactored for better maintainability
- SQLite configured with WAL mode for better concurrency

---

## [1.0] – January 2026

Initial public release.

- Django-based frontend for the DeepL translation API
- German ↔ English text translation with formality control
- Automatic language detection
- Daily / monthly / yearly usage statistics
- Docker Compose deployment with nginx reverse proxy
- Apache-2.0 licence
