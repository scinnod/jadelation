# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Test settings for running automated tests.

Optimized for fast test execution with SQLite.
Imports base settings and overrides only what's necessary for testing.
"""

import os
import tempfile

# Set required environment variables BEFORE importing base settings
# (base settings raises ValueError if these are missing)
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-ci-cd-only-not-for-production")
os.environ.setdefault("DEEPL_AUTHKEY", "test:dummy-key-for-testing-only")
os.environ.setdefault("DJANGO_DEBUG", "True")

from .settings import *  # noqa: E402, F403

# Override for testing
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Use a language code that matches LANGUAGES exactly
# (base settings may have "en-us" which doesn't match i18n_patterns)
LANGUAGE_CODE = "en"

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use a temporary directory for MEDIA_ROOT so tests never write to the real
# data/media/ folder.  The conftest.py session fixture cleans this up.
MEDIA_ROOT = tempfile.mkdtemp(prefix="deepl_test_media_")

# Simplified password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging noise during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
