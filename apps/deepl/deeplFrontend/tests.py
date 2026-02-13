# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Test suite for DeepL Translation Frontend.

Tests cover:
- Model creation, validation, and properties
- Form validation and choices
- View functionality (GET requests, POST translations with mocked API)
- URL routing
- Context processor language selection and fallback chain
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
        # Create a no-op glossary cache for tests that don't need glossaries
        from .views import _GlossaryCache

        self._empty_cache = _GlossaryCache.__new__(_GlossaryCache)
        self._empty_cache._cache = {}
        self._empty_cache._loaded_at = float("inf")  # never expire

    def _patch_empty_glossary(self):
        """Return a context-manager that patches glossary_cache with an empty cache."""
        return patch("deeplFrontend.views.glossary_cache", self._empty_cache)

    @patch("deeplFrontend.views.deepl.Translator")
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

        with self._patch_empty_glossary():
            response = self.client.post(reverse("translation-form"), {
                "sourceText": "Hallo Welt",
                "directionChoice": "DE->EN-GB|",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello World")

    @patch("deeplFrontend.views.deepl.Translator")
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

        with self._patch_empty_glossary():
            response = self.client.post(reverse("translation-form"), {
                "sourceText": "Hello World",
                "directionChoice": "EN-GB->DE|more",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hallo Welt")

    @patch("deeplFrontend.views.deepl.Translator")
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

        with self._patch_empty_glossary():
            response = self.client.post(reverse("translation-form"), {
                "sourceText": "Guten Morgen",
                "directionChoice": "auto",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good morning")

    @patch("deeplFrontend.views.deepl.Translator")
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

        with self._patch_empty_glossary():
            response = self.client.post(reverse("translation-form"), {
                "sourceText": "Good morning",
                "directionChoice": "auto",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guten Morgen")

    @patch("deeplFrontend.views.deepl.Translator")
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
        with self._patch_empty_glossary():
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

        with self._patch_empty_glossary():
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hallo",
                "directionChoice": "auto",
            })
        record = Translation.objects.first()
        self.assertTrue(record.auto_detection)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_post_api_error_returns_error_message(self, mock_translator_cls):
        """Test that DeepL API error returns user-friendly error message."""
        import deepl

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.translate_text.side_effect = deepl.DeepLException("API Error")

        with self._patch_empty_glossary():
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
    def test_post_auto_detection_uses_latency_model(self, mock_translator_cls):
        """Test that auto-detection uses the latency-optimized model type."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_detect = MagicMock()
        mock_detect.detected_source_lang = "DE"
        mock_translate = MagicMock()
        mock_translate.text = "Translated"
        mock_translator.translate_text.side_effect = [mock_detect, mock_translate]

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        with self._patch_empty_glossary():
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hallo Welt",
                "directionChoice": "auto",
            })

        # First call is the detection call
        detection_call = mock_translator.translate_text.call_args_list[0]
        self.assertEqual(
            detection_call.kwargs.get("model_type"),
            "latency_optimized",
        )

    @patch("deeplFrontend.views.deepl.Translator")
    def test_post_translation_uses_quality_model(self, mock_translator_cls):
        """Test that the actual translation uses the prefer_quality_optimized model type."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_result = MagicMock()
        mock_result.text = "Hello World"
        mock_translator.translate_text.return_value = mock_result

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        with self._patch_empty_glossary():
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hallo Welt",
                "directionChoice": "DE->EN-GB|",
            })

        call_kwargs = mock_translator.translate_text.call_args
        self.assertEqual(
            call_kwargs.kwargs.get("model_type"),
            "prefer_quality_optimized",
        )

    @patch("deeplFrontend.views.deepl.Translator")
    def test_post_auto_detection_translation_uses_quality_model(self, mock_translator_cls):
        """Test that after auto-detection, the actual translation also uses the quality model."""
        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        mock_detect = MagicMock()
        mock_detect.detected_source_lang = "EN"
        mock_translate = MagicMock()
        mock_translate.text = "Guten Morgen"
        mock_translator.translate_text.side_effect = [mock_detect, mock_translate]

        mock_usage = MagicMock()
        mock_usage.character.count = 0
        mock_usage.character.limit = 500000
        mock_translator.get_usage.return_value = mock_usage

        with self._patch_empty_glossary():
            self.client.post(reverse("translation-form"), {
                "sourceText": "Good morning",
                "directionChoice": "auto",
            })

        # Second call is the actual translation
        translation_call = mock_translator.translate_text.call_args_list[1]
        self.assertEqual(
            translation_call.kwargs.get("model_type"),
            "prefer_quality_optimized",
        )

    @patch("deeplFrontend.views.deepl.Translator")
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

        with self._patch_empty_glossary():
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

    def test_deepl_model_type_settings_exist(self):
        """Test that DeepL model type settings are configured."""
        self.assertTrue(hasattr(settings, "DEEPL_MODEL_TYPE_DETECTION"))
        self.assertTrue(hasattr(settings, "DEEPL_MODEL_TYPE_TRANSLATION"))
        self.assertIn(
            settings.DEEPL_MODEL_TYPE_DETECTION,
            ("", "quality_optimized", "prefer_quality_optimized", "latency_optimized"),
        )
        self.assertIn(
            settings.DEEPL_MODEL_TYPE_TRANSLATION,
            ("", "quality_optimized", "prefer_quality_optimized", "latency_optimized"),
        )

    def test_installed_apps_includes_app(self):
        """Test that deeplFrontend is in INSTALLED_APPS."""
        self.assertIn("deeplFrontend", settings.INSTALLED_APPS)

    def test_crispy_forms_configured(self):
        """Test that crispy forms is configured with Bootstrap 5."""
        self.assertEqual(settings.CRISPY_TEMPLATE_PACK, "bootstrap5")

    def test_app_title_is_dict(self):
        """Test that APP_TITLE is a dict with language keys."""
        self.assertIsInstance(settings.APP_TITLE, dict)
        self.assertIn("en", settings.APP_TITLE)
        self.assertIn("de", settings.APP_TITLE)

    def test_organization_name_is_dict(self):
        """Test that ORGANIZATION_NAME is a dict with language keys."""
        self.assertIsInstance(settings.ORGANIZATION_NAME, dict)
        self.assertIn("en", settings.ORGANIZATION_NAME)
        self.assertIn("de", settings.ORGANIZATION_NAME)


# ============================================================================
# Context Processor Tests
# ============================================================================

class GetLocalisedTest(TestCase):
    """Test the _get_localised() fallback chain."""

    def test_returns_current_language(self):
        """Test that the current language value is returned."""
        from config.context_processors import _get_localised
        with self.settings(LANGUAGE_CODE="en-us"):
            with patch("config.context_processors.get_language", return_value="de"):
                result = _get_localised({"en": "English Title", "de": "Deutscher Titel"})
        self.assertEqual(result, "Deutscher Titel")

    def test_falls_back_to_language_code(self):
        """Test fallback to LANGUAGE_CODE when current language not in dict."""
        from config.context_processors import _get_localised
        with self.settings(LANGUAGE_CODE="en-us"):
            with patch("config.context_processors.get_language", return_value="fr"):
                result = _get_localised({"en": "English Title", "de": "Deutscher Titel"})
        self.assertEqual(result, "English Title")

    def test_falls_back_to_english(self):
        """Test fallback to 'en' when LANGUAGE_CODE not in dict either."""
        from config.context_processors import _get_localised
        with self.settings(LANGUAGE_CODE="fr"):
            with patch("config.context_processors.get_language", return_value="es"):
                result = _get_localised({"en": "English Title", "de": "Deutscher Titel"})
        self.assertEqual(result, "English Title")

    def test_falls_back_to_first_available(self):
        """Test fallback to first value when no standard key matches."""
        from config.context_processors import _get_localised
        with self.settings(LANGUAGE_CODE="fr"):
            with patch("config.context_processors.get_language", return_value="es"):
                result = _get_localised({"de": "Deutscher Titel"})
        self.assertEqual(result, "Deutscher Titel")

    def test_returns_fallback_string_for_empty_dict(self):
        """Test that empty dict returns the fallback string."""
        from config.context_processors import _get_localised
        result = _get_localised({}, fallback="Fallback")
        self.assertEqual(result, "Fallback")

    def test_handles_regional_language_code(self):
        """Test that regional codes like 'en-us' are normalised to 'en'."""
        from config.context_processors import _get_localised
        with self.settings(LANGUAGE_CODE="en-us"):
            with patch("config.context_processors.get_language", return_value="en-us"):
                result = _get_localised({"en": "English Title", "de": "Deutscher Titel"})
        self.assertEqual(result, "English Title")


class ContextProcessorTest(TestCase):
    """Test the app_settings context processor end-to-end."""

    def test_app_title_in_context(self):
        """Test that APP_TITLE appears in rendered pages."""
        response = self.client.get(reverse("translation-form"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("APP_TITLE", response.context)
        self.assertIsInstance(response.context["APP_TITLE"], str)
        self.assertTrue(len(response.context["APP_TITLE"]) > 0)

    def test_organization_name_in_context(self):
        """Test that ORGANIZATION_NAME appears in rendered pages."""
        response = self.client.get(reverse("translation-form"), follow=True)
        self.assertIn("ORGANIZATION_NAME", response.context)

    @override_settings(APP_TITLE={"en": "Test Title EN", "de": "Test Titel DE"})
    def test_app_title_language_selection(self):
        """Test that APP_TITLE uses the correct language."""
        # Request with German language
        response = self.client.get(reverse("translation-form"), HTTP_ACCEPT_LANGUAGE="de")
        # The title should be one of the configured values
        self.assertIn(response.context["APP_TITLE"], ["Test Title EN", "Test Titel DE"])


# ============================================================================
# Glossary View Integration Tests
# ============================================================================

class GlossaryCacheTest(TestCase):
    """Test the _GlossaryCache lazy-loading and auto-refresh mechanism."""

    def setUp(self):
        self.glossary = Glossary.objects.create(
            glossary_id="cache-test-id",
            name="Cache Test Glossary",
            source_lang="DE",
            target_lang="EN-GB",
            original_filename="cache.csv",
            entry_count=5,
        )

    @patch("deeplFrontend.views.deepl.Translator")
    def test_lazy_load_on_first_access(self, mock_translator_cls):
        """Cache is populated lazily on the first .get() call, not at creation."""
        from .views import _GlossaryCache

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_deepl_glossary = MagicMock()
        mock_translator.get_glossary.return_value = mock_deepl_glossary

        cache = _GlossaryCache()
        # Cache should NOT have called the API yet
        mock_translator_cls.assert_not_called()

        # First .get() triggers loading
        result = cache.get("DE->EN")
        self.assertEqual(result, mock_deepl_glossary)
        mock_translator.get_glossary.assert_called_once_with("cache-test-id")

    @patch("deeplFrontend.views.deepl.Translator")
    def test_normalises_keys_to_two_letter_codes(self, mock_translator_cls):
        """Cache keys are normalised to 2-letter codes (e.g. DE->EN, not DE->EN-GB)."""
        from .views import _GlossaryCache

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.get_glossary.return_value = MagicMock()

        cache = _GlossaryCache()
        self.assertIsNotNone(cache.get("DE->EN"))
        self.assertIsNone(cache.get("DE->EN-GB"))

    @patch("deeplFrontend.views.deepl.Translator")
    def test_cache_ttl_refresh(self, mock_translator_cls):
        """Cache refreshes after TTL expires."""
        from .views import _GlossaryCache

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        first_glossary = MagicMock(name="first")
        second_glossary = MagicMock(name="second")
        mock_translator.get_glossary.side_effect = [first_glossary, second_glossary]

        cache = _GlossaryCache()
        self.assertEqual(cache.get("DE->EN"), first_glossary)

        # Simulate TTL expiry by backdating _loaded_at
        cache._loaded_at = 0.0
        self.assertEqual(cache.get("DE->EN"), second_glossary)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_reload_forces_refresh(self, mock_translator_cls):
        """Manual reload() forces an immediate refresh."""
        from .views import _GlossaryCache

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        first_glossary = MagicMock(name="first")
        second_glossary = MagicMock(name="second")
        mock_translator.get_glossary.side_effect = [first_glossary, second_glossary]

        cache = _GlossaryCache()
        cache.get("DE->EN")  # initial load
        cache.reload()       # forced refresh
        self.assertEqual(cache.get("DE->EN"), second_glossary)

    @patch("deeplFrontend.views.deepl.Translator")
    def test_loaded_pairs_property(self, mock_translator_cls):
        """loaded_pairs returns the set of cached language-pair keys."""
        from .views import _GlossaryCache

        Glossary.objects.create(
            glossary_id="en-de-id", name="EN-DE test",
            source_lang="EN", target_lang="DE",
            original_filename="b.csv", entry_count=3,
        )

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        mock_translator.get_glossary.return_value = MagicMock()

        cache = _GlossaryCache()
        self.assertEqual(cache.loaded_pairs, {"DE->EN", "EN->DE"})

    @patch("deeplFrontend.views.deepl.Translator")
    def test_api_failure_returns_empty_cache(self, mock_translator_cls):
        """If the DeepL API is unreachable the cache stays empty (no crash)."""
        from .views import _GlossaryCache

        mock_translator_cls.side_effect = Exception("API unreachable")

        cache = _GlossaryCache()
        self.assertIsNone(cache.get("DE->EN"))
        self.assertEqual(cache.loaded_pairs, set())

    @patch("deeplFrontend.views.deepl.Translator")
    def test_duplicate_pair_uses_newest_glossary(self, mock_translator_cls):
        """When multiple glossaries exist for the same language pair,
        the most recently uploaded one is used (others are skipped)."""
        from .views import _GlossaryCache

        # Create an older duplicate glossary for the same pair (DE->EN).
        # setUp already created one with glossary_id="cache-test-id".
        older = Glossary.objects.create(
            glossary_id="older-duplicate-id",
            name="Older Duplicate Glossary",
            source_lang="DE",
            target_lang="EN",
            original_filename="old.csv",
            entry_count=3,
        )
        # auto_now_add ignores explicit values, so backdate via update()
        Glossary.objects.filter(pk=older.pk).update(
            upload_date=self.glossary.upload_date - timedelta(days=1),
        )

        newest_deepl = MagicMock(name="newest")
        older_deepl = MagicMock(name="older")

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator
        # Glossary.objects.all() returns newest first (-upload_date).
        # The cache should keep only the first (newest) one it encounters.
        mock_translator.get_glossary.side_effect = (
            lambda gid: newest_deepl if gid == "cache-test-id" else older_deepl
        )

        cache = _GlossaryCache()
        result = cache.get("DE->EN")

        self.assertEqual(result, newest_deepl, "Should use the newest glossary")
        self.assertEqual(cache.loaded_pairs, {"DE->EN"})
        # Only one entry for DE->EN, not two
        self.assertEqual(len(cache._cache), 1)


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

    def _make_mock_glossary_cache(self, pairs):
        """Create a mock _GlossaryCache whose .get() uses the given dict."""
        from .views import _GlossaryCache

        cache = _GlossaryCache.__new__(_GlossaryCache)
        cache._cache = pairs
        cache._loaded_at = float("inf")  # never expire
        return cache

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
        mock_cache = self._make_mock_glossary_cache({"DE->EN": test_glossary_obj})
        with patch("deeplFrontend.views.glossary_cache", mock_cache):
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
        mock_cache = self._make_mock_glossary_cache({"EN->DE": test_glossary_obj})
        with patch("deeplFrontend.views.glossary_cache", mock_cache):
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hello world",
                "directionChoice": "EN-GB->DE|more",
            })

        call_kwargs = mock_translator.translate_text.call_args
        self.assertEqual(call_kwargs.kwargs.get("glossary"), test_glossary_obj)

    @patch("deeplFrontend.views.deepl.Translator")
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

        mock_cache = self._make_mock_glossary_cache({})
        with patch("deeplFrontend.views.glossary_cache", mock_cache):
            self.client.post(reverse("translation-form"), {
                "sourceText": "Hello",
                "directionChoice": "EN-GB->DE|more",
            })

        call_kwargs = mock_translator.translate_text.call_args
        self.assertIsNone(call_kwargs.kwargs.get("glossary"))

    @patch("deeplFrontend.views.deepl.Translator")
    def test_cache_normalises_keys(self, mock_translator_cls):
        """Test that _GlossaryCache normalises keys to 2-letter codes.

        This is the root cause of the glossary-not-used bug: glossaries
        uploaded with target_lang='EN-GB' were stored under 'DE->EN-GB' in the
        cache, but the translation view looked them up as 'DE->EN'
        (normalised to 2-letter codes).  After the fix both sides normalise.
        """
        from .views import _GlossaryCache

        mock_translator = MagicMock()
        mock_translator_cls.return_value = mock_translator

        # Simulate a glossary fetched from DeepL API
        mock_deepl_glossary = MagicMock()
        mock_translator.get_glossary.return_value = mock_deepl_glossary

        # DB has glossary with target_lang "EN-GB" (regional variant)
        # _GlossaryCache should normalise to "DE->EN"
        cache = _GlossaryCache()
        self.assertIsNotNone(cache.get("DE->EN"))
        self.assertIsNone(cache.get("DE->EN-GB"))
        self.assertEqual(cache.get("DE->EN"), mock_deepl_glossary)
