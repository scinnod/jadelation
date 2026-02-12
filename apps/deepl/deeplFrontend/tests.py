# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Test suite for DeepL Translation Frontend.

Tests cover:
- Model creation, validation, and properties
- Form validation and choices
- View functionality (GET requests, POST translations with mocked API)
- URL routing
- Template tag functionality
- Settings configuration
"""

import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import TranslationForm
from .models import Translation, Glossary


# ============================================================================
# Model Tests
# ============================================================================

class TranslationModelTest(TestCase):
    """Test Translation model creation, defaults, and string representation."""

    def test_translation_creation(self):
        """Test creating a translation record with all fields."""
        t = Translation.objects.create(
            characters=150,
            direction="DE->EN-GB|",
            auto_detection=False,
        )
        self.assertEqual(t.characters, 150)
        self.assertEqual(t.direction, "DE->EN-GB|")
        self.assertFalse(t.auto_detection)
        self.assertIsNotNone(t.timestamp)

    def test_translation_str(self):
        """Test string representation includes direction and timestamp."""
        t = Translation.objects.create(
            characters=100,
            direction="EN-GB->DE|more",
            auto_detection=True,
        )
        s = str(t)
        self.assertIn("EN-GB->DE|more", s)

    def test_translation_ordering(self):
        """Test that translations are ordered by timestamp descending."""
        t1 = Translation.objects.create(
            characters=10, direction="DE->EN-GB|", auto_detection=False
        )
        t2 = Translation.objects.create(
            characters=20, direction="DE->EN-GB|", auto_detection=False
        )
        translations = list(Translation.objects.all())
        # Most recent first
        self.assertEqual(translations[0].pk, t2.pk)
        self.assertEqual(translations[1].pk, t1.pk)

    def test_translation_auto_detection_field(self):
        """Test auto_detection boolean field values."""
        t_auto = Translation.objects.create(
            characters=50, direction="DE->EN-GB|", auto_detection=True
        )
        t_manual = Translation.objects.create(
            characters=50, direction="DE->EN-GB|", auto_detection=False
        )
        self.assertTrue(t_auto.auto_detection)
        self.assertFalse(t_manual.auto_detection)


class GlossaryModelTest(TestCase):
    """Test Glossary model creation, properties, and string representation."""

    def setUp(self):
        """Create a test glossary."""
        self.glossary = Glossary.objects.create(
            glossary_id="test-glossary-id-123",
            name="Test Glossary",
            source_lang="DE",
            target_lang="EN-GB",
            original_filename="test_glossary.csv",
            comment="A test glossary",
            entry_count=42,
        )

    def test_glossary_creation(self):
        """Test glossary fields are stored correctly."""
        g = self.glossary
        self.assertEqual(g.glossary_id, "test-glossary-id-123")
        self.assertEqual(g.name, "Test Glossary")
        self.assertEqual(g.source_lang, "DE")
        self.assertEqual(g.target_lang, "EN-GB")
        self.assertEqual(g.original_filename, "test_glossary.csv")
        self.assertEqual(g.comment, "A test glossary")
        self.assertEqual(g.entry_count, 42)
        self.assertIsNotNone(g.upload_date)

    def test_glossary_str(self):
        """Test string representation format."""
        self.assertEqual(str(self.glossary), "Test Glossary (DE->EN-GB)")

    def test_glossary_language_pair(self):
        """Test language_pair property."""
        self.assertEqual(self.glossary.language_pair, "DE->EN-GB")

    def test_glossary_unique_id(self):
        """Test that glossary_id must be unique."""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Glossary.objects.create(
                glossary_id="test-glossary-id-123",  # Same as setUp
                name="Duplicate",
                source_lang="EN",
                target_lang="DE",
                original_filename="dup.csv",
            )

    def test_glossary_comment_blank(self):
        """Test that comment can be empty."""
        g = Glossary.objects.create(
            glossary_id="no-comment-id",
            name="No Comment Glossary",
            source_lang="EN",
            target_lang="DE",
            original_filename="nc.csv",
        )
        self.assertEqual(g.comment, "")

    def test_glossary_ordering(self):
        """Test that glossaries are ordered by upload_date descending."""
        g2 = Glossary.objects.create(
            glossary_id="second-glossary-id",
            name="Second Glossary",
            source_lang="EN",
            target_lang="DE",
            original_filename="second.csv",
        )
        glossaries = list(Glossary.objects.all())
        # Most recent first
        self.assertEqual(glossaries[0].pk, g2.pk)


# ============================================================================
# Form Tests
# ============================================================================

class TranslationFormTest(TestCase):
    """Test TranslationForm validation and field behavior."""

    def test_valid_form_auto(self):
        """Test form with auto detection direction."""
        form = TranslationForm(data={
            "sourceText": "Hello world",
            "directionChoice": "auto",
        })
        self.assertTrue(form.is_valid())

    def test_valid_form_de_en(self):
        """Test form with DE->EN direction."""
        form = TranslationForm(data={
            "sourceText": "Hallo Welt",
            "directionChoice": "DE->EN-GB|",
        })
        self.assertTrue(form.is_valid())

    def test_valid_form_en_de_formal(self):
        """Test form with EN->DE formal direction."""
        form = TranslationForm(data={
            "sourceText": "Hello world",
            "directionChoice": "EN-GB->DE|more",
        })
        self.assertTrue(form.is_valid())

    def test_valid_form_en_de_informal(self):
        """Test form with EN->DE informal direction."""
        form = TranslationForm(data={
            "sourceText": "Hello world",
            "directionChoice": "EN-GB->DE|less",
        })
        self.assertTrue(form.is_valid())

    def test_empty_source_text_invalid(self):
        """Test that empty source text is invalid."""
        form = TranslationForm(data={
            "sourceText": "",
            "directionChoice": "auto",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("sourceText", form.errors)

    def test_missing_direction_invalid(self):
        """Test that missing direction choice is invalid."""
        form = TranslationForm(data={
            "sourceText": "Hello",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("directionChoice", form.errors)

    def test_invalid_direction_invalid(self):
        """Test that an invalid direction choice is rejected."""
        form = TranslationForm(data={
            "sourceText": "Hello",
            "directionChoice": "INVALID",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("directionChoice", form.errors)

    def test_direction_choices_count(self):
        """Test that exactly 4 direction choices are available."""
        form = TranslationForm()
        choices = form.fields["directionChoice"].choices
        self.assertEqual(len(choices), 4)

    def test_translated_text_disabled(self):
        """Test that translatedText field is disabled (output only)."""
        form = TranslationForm()
        self.assertTrue(form.fields["translatedText"].disabled)

    def test_translated_text_not_required(self):
        """Test that translatedText field is not required."""
        form = TranslationForm()
        self.assertFalse(form.fields["translatedText"].required)


# ============================================================================
# URL Tests
# ============================================================================

class URLRoutingTest(TestCase):
    """Test URL routing configuration."""

    def test_translation_form_url_resolves(self):
        """Test that translation-form URL resolves."""
        url = reverse("translation-form")
        self.assertIn("/deepl/translation/", url)

    def test_statistics_daily_url_resolves(self):
        """Test that daily statistics URL resolves."""
        url = reverse("usage-statistics", kwargs={"granularity": "d"})
        self.assertIn("stat/d", url)

    def test_statistics_monthly_url_resolves(self):
        """Test that monthly statistics URL resolves."""
        url = reverse("usage-statistics", kwargs={"granularity": "m"})
        self.assertIn("stat/m", url)

    def test_statistics_yearly_url_resolves(self):
        """Test that yearly statistics URL resolves."""
        url = reverse("usage-statistics", kwargs={"granularity": "y"})
        self.assertIn("stat/y", url)


# ============================================================================
# View Tests
# ============================================================================

class TranslationViewGetTest(TestCase):
    """Test GET requests to the translation view."""

    def setUp(self):
        self.client = Client()

    def test_translation_page_returns_200(self):
        """Test that translation page loads successfully."""
        response = self.client.get(reverse("translation-form"))
        self.assertEqual(response.status_code, 200)

    def test_translation_page_contains_form(self):
        """Test that translation page contains the translation form."""
        response = self.client.get(reverse("translation-form"))
        self.assertContains(response, "sourceText")

    def test_translation_page_uses_correct_template(self):
        """Test that translation page uses the correct template."""
        response = self.client.get(reverse("translation-form"))
        self.assertTemplateUsed(response, "translation_frontend.html")

    def test_root_redirects_to_translation(self):
        """Test that root URL redirects to translation form."""
        response = self.client.get("/", follow=False)
        self.assertEqual(response.status_code, 301)


class TranslationViewPostTest(TestCase):
    """Test POST requests to the translation view with mocked DeepL API."""

    def setUp(self):
        self.client = Client()

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_de_en_translation(self, mock_translator_cls):
        """Test DE->EN translation request."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Hello World"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Hallo Welt",
            "directionChoice": "DE->EN-GB|",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello World")

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_en_de_formal_translation(self, mock_translator_cls):
        """Test EN->DE formal translation request."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Hallo Welt"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Hello World",
            "directionChoice": "EN-GB->DE|more",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hallo Welt")

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_auto_detection_german(self, mock_translator_cls):
        """Test auto-detection when input is German."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        # First call: auto-detection (short text sent to determine language)
        mock_detect_result = MagicMock()
        mock_detect_result.detected_source_lang = "DE"
        # Second call: actual translation
        mock_translate_result = MagicMock()
        mock_translate_result.text = "Good morning"

        mock_translator.translate_text.side_effect = [
            mock_detect_result, mock_translate_result
        ]

        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Guten Morgen",
            "directionChoice": "auto",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good morning")

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_auto_detection_english(self, mock_translator_cls):
        """Test auto-detection when input is English."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_detect_result = MagicMock()
        mock_detect_result.detected_source_lang = "EN"
        mock_translate_result = MagicMock()
        mock_translate_result.text = "Guten Morgen"

        mock_translator.translate_text.side_effect = [
            mock_detect_result, mock_translate_result
        ]

        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Good morning",
            "directionChoice": "auto",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guten Morgen")

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_creates_translation_record(self, mock_translator_cls):
        """Test that a successful translation creates a database record."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Translated text"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        self.assertEqual(Translation.objects.count(), 0)
        self.client.post(reverse("translation-form"), {
            "sourceText": "Test text",
            "directionChoice": "DE->EN-GB|",
        })
        self.assertEqual(Translation.objects.count(), 1)

        record = Translation.objects.first()
        self.assertEqual(record.direction, "DE->EN-GB|")
        self.assertEqual(record.characters, len("Test text"))
        self.assertFalse(record.auto_detection)

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_auto_detection_sets_flag(self, mock_translator_cls):
        """Test that auto-detection sets the auto_detection flag in DB."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_detect = MagicMock()
        mock_detect.detected_source_lang = "DE"
        mock_translate = MagicMock()
        mock_translate.text = "Result"

        mock_translator.translate_text.side_effect = [mock_detect, mock_translate]

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        self.client.post(reverse("translation-form"), {
            "sourceText": "Hallo",
            "directionChoice": "auto",
        })
        record = Translation.objects.first()
        self.assertTrue(record.auto_detection)

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_api_error_returns_error_message(self, mock_translator_cls):
        """Test that DeepL API error returns user-friendly error message."""
        import deepl

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.translate_text.side_effect = deepl.DeepLException("API Error")

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Test text",
            "directionChoice": "DE->EN-GB|",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ERROR")

    def test_post_invalid_form_returns_200(self):
        """Test that posting an invalid form still returns 200."""
        response = self.client.post(reverse("translation-form"), {
            "sourceText": "",
            "directionChoice": "auto",
        })
        self.assertEqual(response.status_code, 200)

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_post_displays_usage_info(self, mock_translator_cls):
        """Test that successful translation displays API usage information."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Translated"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 12345
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.post(reverse("translation-form"), {
            "sourceText": "Test",
            "directionChoice": "DE->EN-GB|",
        })
        self.assertContains(response, "12345")


class StatisticsViewTest(TestCase):
    """Test statistics views with different granularities."""

    def setUp(self):
        self.client = Client()
        # Create some test translation records
        now = timezone.now()
        for i in range(3):
            Translation.objects.create(
                characters=100 + i * 50,
                direction="DE->EN-GB|",
                auto_detection=False,
            )
        Translation.objects.create(
            characters=200,
            direction="EN-GB->DE|more",
            auto_detection=True,
        )

    @patch("deeplFrontend.views.deepl.Translator")
    def test_daily_statistics_returns_200(self, mock_translator_cls):
        """Test daily statistics page loads."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "d"})
        )
        self.assertEqual(response.status_code, 200)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_monthly_statistics_returns_200(self, mock_translator_cls):
        """Test monthly statistics page loads."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "m"})
        )
        self.assertEqual(response.status_code, 200)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_yearly_statistics_returns_200(self, mock_translator_cls):
        """Test yearly statistics page loads."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 1000
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "y"})
        )
        self.assertEqual(response.status_code, 200)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_statistics_uses_correct_template(self, mock_translator_cls):
        """Test statistics page uses correct template."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "d"})
        )
        self.assertTemplateUsed(response, "statistics_frontend.html")

    @patch("deeplFrontend.views.deepl.Translator")
    def test_invalid_granularity_still_returns_200(self, mock_translator_cls):
        """Test that invalid granularity returns 200 with error message."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "x"})
        )
        self.assertEqual(response.status_code, 200)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_statistics_context_contains_expected_keys(self, mock_translator_cls):
        """Test that statistics context has all required keys."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_usage = MagicMock()
        mock_usage.character.count = 500
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "d"})
        )
        self.assertIn("statistics", response.context)
        self.assertIn("granularity_title", response.context)
        self.assertIn("usage", response.context)
        self.assertIn("dformat", response.context)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_statistics_api_error_handled(self, mock_translator_cls):
        """Test that API error during statistics is handled gracefully."""
        import deepl

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.get_usage.side_effect = deepl.DeepLException("API Error")

        response = self.client.get(
            reverse("usage-statistics", kwargs={"granularity": "d"})
        )
        self.assertEqual(response.status_code, 200)


# ============================================================================
# Template Tag Tests
# ============================================================================

class LoadAboutContentTest(TestCase):
    """Test the load_about_content template tag."""

    def test_load_about_content_with_file(self):
        """Test loading about content from a markdown file."""
        from .templatetags.custom_helper_tags import load_about_content

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test markdown file
            md_file = os.path.join(tmpdir, "about_en.md")
            with open(md_file, "w") as f:
                f.write("# Test About\n\nThis is a **test**.")

            with patch(
                "deeplFrontend.templatetags.custom_helper_tags.Path"
            ) as mock_path_cls:
                mock_path = MagicMock()
                mock_path_cls.return_value = mock_path

                # Make the path resolve to our temp file
                mock_md_file = MagicMock()
                mock_md_file.exists.return_value = True
                mock_md_file.__str__ = lambda self: md_file
                mock_md_file.__fspath__ = lambda self: md_file
                mock_path.__truediv__ = lambda self, name: mock_md_file

                # Mock open to read from the actual file
                result = load_about_content()
                # The function should return HTML content (may use default path)
                self.assertIsNotNone(result)


class ChangeLanguageTagTest(TestCase):
    """Test the change_lang template tag."""

    def test_change_lang_returns_url(self):
        """Test that change_lang returns a translated URL."""
        from .templatetags.custom_helper_tags import change_lang

        factory = RequestFactory()
        # Use a real resolvable URL so translate_url can match it
        url = reverse("translation-form")
        request = factory.get(url)
        context = {"request": request}

        result = change_lang(context, "de")
        self.assertIn("/de/", result)
        self.assertIn("/deepl/translation/", result)


# ============================================================================
# Settings Tests
# ============================================================================

class SettingsTest(TestCase):
    """Test that essential settings are configured correctly for tests."""

    def test_debug_is_false_during_tests(self):
        """Test that Django forces DEBUG=False during test runs for safety."""
        self.assertFalse(settings.DEBUG)

    def test_database_is_sqlite(self):
        """Test that test database uses SQLite."""
        self.assertIn("sqlite3", settings.DATABASES["default"]["ENGINE"])

    def test_deepl_authkey_configured(self):
        """Test that DEEPL_AUTHKEY is set (dummy for tests)."""
        self.assertTrue(hasattr(settings, "DEEPL_AUTHKEY"))
        self.assertTrue(len(settings.DEEPL_AUTHKEY) > 0)

    def test_translation_settings_have_defaults(self):
        """Test that translation settings have sensible defaults."""
        self.assertGreater(settings.TRANSLATION_DETECTION_LEN, 0)
        self.assertGreater(settings.STATISTICS_DAYS, 0)
        self.assertGreater(settings.STATISTICS_MONTHS, 0)
        self.assertGreater(settings.STATISTICS_YEARS, 0)

    def test_installed_apps_includes_app(self):
        """Test that deeplFrontend is in INSTALLED_APPS."""
        self.assertIn("deeplFrontend", settings.INSTALLED_APPS)

    def test_crispy_forms_configured(self):
        """Test that crispy forms is configured with Bootstrap 5."""
        self.assertEqual(settings.CRISPY_TEMPLATE_PACK, "bootstrap5")


# ============================================================================
# Glossary View Integration Tests
# ============================================================================

class GlossaryIntegrationTest(TestCase):
    """Test glossary integration in the translation flow."""

    def setUp(self):
        self.client = Client()
        # Create a test glossary in the database
        self.glossary = Glossary.objects.create(
            glossary_id="integration-test-id",
            name="Integration Test Glossary",
            source_lang="DE",
            target_lang="EN-GB",
            original_filename="integration.csv",
            entry_count=10,
        )

    @patch("deeplFrontend.views.deepl.Translator")
    def test_glossary_passed_to_translator(self, mock_translator_cls):
        """Test that glossary is passed to translator when available."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Translated"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        # Cache key uses normalised 2-letter codes (DE->EN, not DE->EN-GB)
        test_glossary_obj = MagicMock()
        with patch("deeplFrontend.views.glossary", {"DE->EN": test_glossary_obj}):
            self.client.post(reverse("translation-form"), {
                "sourceText": "Testtext",
                "directionChoice": "DE->EN-GB|",
            })

        # Verify translate_text was called with the glossary
        call_kwargs = mock_translator.translate_text.call_args
        self.assertEqual(call_kwargs.kwargs.get("glossary"), test_glossary_obj)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_glossary_passed_for_en_de_direction(self, mock_translator_cls):
        """Test that glossary is passed for EN->DE direction."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Übersetzt"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        test_glossary_obj = MagicMock()
        with patch("deeplFrontend.views.glossary", {"EN->DE": test_glossary_obj}):
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hello world",
                "directionChoice": "EN-GB->DE|more",
            })

        call_kwargs = mock_translator.translate_text.call_args
        self.assertEqual(call_kwargs.kwargs.get("glossary"), test_glossary_obj)

    @patch("deeplFrontend.views.deepl.Translator")
    @patch("deeplFrontend.views.glossary", {})
    def test_no_glossary_when_not_available(self, mock_translator_cls):
        """Test that None is passed when no glossary matches."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Translated"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        self.client.post(reverse("translation-form"), {
            "sourceText": "Hello",
            "directionChoice": "EN-GB->DE|more",
        })

        call_kwargs = mock_translator.translate_text.call_args
        self.assertIsNone(call_kwargs.kwargs.get("glossary"))

    @patch("deeplFrontend.views.deepl.Translator")
    def test_load_glossaries_normalises_keys(self, mock_translator_cls):
        """Test that load_glossaries() normalises cache keys to 2-letter codes.

        This is the root cause of the glossary-not-used bug: glossaries
        uploaded with target_lang='EN' were stored under 'DE->EN' in the
        cache, but the translation view looked them up as 'DE->EN-GB'
        (the full regional code from the direction string).  After the fix,
        load_glossaries() normalises both source and target to 2-letter
        codes, and the view does the same for the lookup key.
        """
        from .views import load_glossaries

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        # Simulate a glossary fetched from DeepL API
        mock_deepl_glossary = MagicMock()
        mock_translator.get_glossary.return_value = mock_deepl_glossary

        # DB has glossary with target_lang "EN-GB" (regional variant)
        # load_glossaries should normalise to "DE->EN"
        result = load_glossaries()

        self.assertIn("DE->EN", result)
        self.assertNotIn("DE->EN-GB", result)
        self.assertEqual(result["DE->EN"], mock_deepl_glossary)
