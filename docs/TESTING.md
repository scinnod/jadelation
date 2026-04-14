# Testing Guide

## Overview

The project uses **pytest** with **pytest-django** for testing. The test suite covers:

- **Model tests**: Creation, validation, string representation, ordering
- **Form tests**: Validation rules, field configuration, direction choices
- **View tests**: GET/POST requests with mocked DeepL API, error handling
- **URL tests**: Route resolution and naming
- **Template tag tests**: Language switching, about content loading
- **Settings tests**: Configuration sanity checks
- **Integration tests**: Glossary cache interaction with translation flow

## Quick Start

Run tests locally with Docker (fastest and easiest):

```bash
cd /path/to/1_deepl
docker-compose exec deepl pip install -r requirements-test.txt
docker-compose exec deepl python -m pytest -v
```

## Running Tests Locally

### Option 1: With Docker Containers (Recommended)

```bash
# Make sure containers are running
docker-compose up -d

# Install test dependencies (temporary, lost on container restart)
docker-compose exec deepl pip install -r requirements-test.txt

# Run all tests
docker-compose exec deepl python -m pytest

# Run with verbose output
docker-compose exec deepl python -m pytest -v

# Run with coverage
docker-compose exec deepl python -m pytest --cov=deeplFrontend --cov-report=term-missing

# Run specific test class
docker-compose exec deepl python -m pytest deeplFrontend/tests.py::TranslationModelTest

# Run specific test method
docker-compose exec deepl python -m pytest deeplFrontend/tests.py::TranslationFormTest::test_valid_form_auto -v

# Run tests matching a pattern
docker-compose exec deepl python -m pytest -k "glossary" -v

# Stop on first failure
docker-compose exec deepl python -m pytest -x
```

### Option 2: Local Python Environment

```bash
cd apps/deepl
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt -r requirements-test.txt
python -m pytest -v
```

No external database or services needed — tests use in-memory SQLite and mock all DeepL API calls.

## Running Tests on GitHub Actions

Tests run automatically on every push and pull request to `main` or `develop`
via GitHub Actions (`.github/workflows/django-tests.yml`).

The CI workflow:
1. Tests against Python 3.11 and 3.12 in parallel
2. Runs Django system checks
3. Runs database migrations
4. Executes the full test suite with coverage
5. Uploads coverage reports to Codecov (optional)

**Status Badge:** Add this to your README to show test status:

```markdown
[![Django Tests](https://github.com/javidkl/jade-django-1-deepl/actions/workflows/django-tests.yml/badge.svg)](https://github.com/javidkl/jade-django-1-deepl/actions/workflows/django-tests.yml)
```

## Test Configuration

### pytest.ini

The pytest configuration is in `apps/deepl/pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings_test
testpaths = deeplFrontend
addopts = --verbose --strict-markers --tb=short -p no:warnings
```

### Test Settings

Test-specific Django settings are in `apps/deepl/config/settings_test.py`:

- Sets dummy `DJANGO_SECRET_KEY` and `DEEPL_AUTHKEY` environment variables
- Uses in-memory SQLite for fast tests
- Simplified password hashing
- Disables logging noise

## Writing Tests

### Test Structure

Tests are organized by component in `apps/deepl/deeplFrontend/tests.py`:

```python
class TranslationModelTest(TestCase):
    """Test Translation model"""

    def test_translation_creation(self):
        """Test creating a translation record"""
        t = Translation.objects.create(
            characters=150,
            direction="DE->EN-GB|",
            auto_detection=False,
        )
        self.assertEqual(t.characters, 150)
```

### Mocking the DeepL API

Since tests must not call the real DeepL API, all API interactions are mocked:

```python
from unittest.mock import MagicMock, patch

@patch("deeplFrontend.views.deepl.Translator")
@patch("deeplFrontend.views.glossary", {})
def test_translation(self, mock_translator_cls):
    mock_translator = MagicMock()
    mock_translator_cls.return_value = mock_translator
    
    mock_result = MagicMock()
    mock_result.text = "Translated text"
    mock_translator.translate_text.return_value = mock_result
    
    mock_usage = MagicMock()
    mock_usage.character.count = 1000
    mock_usage.character.limit = 500000
    mock_translator.get_usage.return_value = mock_usage
    
    response = self.client.post(reverse("translation-form"), {
        "sourceText": "Source text",
        "directionChoice": "DE->EN-GB|",
    })
    self.assertEqual(response.status_code, 200)
```

## Coverage

### Generating Coverage Reports

```bash
# Terminal report with missing lines
docker-compose exec deepl python -m pytest --cov=deeplFrontend --cov-report=term-missing

# HTML report (interactive)
docker-compose exec deepl python -m pytest --cov=deeplFrontend --cov-report=html
docker cp deepl:/app/htmlcov ./htmlcov
# Open htmlcov/index.html in browser

# XML report (for CI)
docker-compose exec deepl python -m pytest --cov=deeplFrontend --cov-report=xml
```

### Coverage Goals

- **Minimum**: 70% overall coverage
- **Target**: 85% for models and views

## Test Classes Summary

| Class | What It Tests |
|---|---|
| `TranslationModelTest` | Translation model creation, validation, ordering |
| `GlossaryModelTest` | Glossary model creation and properties |
| `TranslationFormTest` | Text translation form validation |
| `DocumentTranslationFormTest` | Document form: file type/size validation, direction choices |
| `ViewGetTest` | GET requests: form rendering, context, usage display |
| `ViewPostTest` | POST text translation with mocked DeepL API |
| `URLTest` | URL resolution and naming |
| `ContextProcessorLanguageTest` | Language selection, fallback chain |
| `CustomHelperTagsTest` | Template tags |
| `SettingsTest` | Configuration sanity checks |
| `GlossaryIntegrationTest` | Glossary cache interaction with translation |
| `DocumentTranslationURLTest` | Document translation URL resolution |
| `DocumentTranslationViewGetTest` | Tab visibility, feature toggle, form context |
| `DocumentTranslationViewPostTest` | Async upload: JSON job creation, validation errors, API errors, single-active-job enforcement |
| `DocumentTranslationJobModelTest` | Job model defaults, UUID PK, string repr |
| `DocumentJobStatusEndpointTest` | Status polling: session security, status values, feature toggle |
| `DocumentDownloadEndpointTest` | File download: serving, re-download, session security, edge cases |
| `StaleDocumentJobCleanupTest` | 10-minute file cleanup: stale removed, recent kept |
| `TranslateDocxHelperTest` | `_translate_docx`: paragraphs, tables, multi-run merge, char count |
| `TranslatePptxHelperTest` | `_translate_pptx`: slides, empty slides |
| `TranslateTextFragmentTest` | `_translate_text_fragment`: empty, whitespace, API call |
| `LangSuffixTest` | `_lang_suffix` helper |
| `DocumentTranslationSettingsTest` | Feature flag and context processor |
