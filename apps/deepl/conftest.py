# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024-2026 David Kleinhans, Jade University of Applied Sciences
"""Pytest fixtures shared across the test suite."""

import shutil

import pytest
from django.conf import settings


@pytest.fixture(autouse=True, scope="session")
def _cleanup_test_media():
    """Remove the temporary MEDIA_ROOT directory after the test session."""
    yield
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
