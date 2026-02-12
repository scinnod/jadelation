# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""
Test settings for running automated tests.

Optimized for fast test execution with SQLite.
Imports base settings and overrides only what's necessary for testing.
"""

import os

# Set required environment variables BEFORE importing base settings
# (base settings raises ValueError if these are missing)
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-ci-cd-only-not-for-production")
os.environ.setdefault("DEEPL_AUTHKEY", "test:dummy-key-for-testing-only")
os.environ.setdefault("DJANGO_DEBUG", "True")

from .settings import *  # noqa: E402, F403

# Override for testing
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

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
