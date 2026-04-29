# SPDX-License-Identifier: Apache-2.0
import re
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class DocumentTranslationsMiddleware:
    """Grant or revoke session access to document translation based on email.

    When ``DOCUMENT_TRANSLATION_ENABLED`` is a regex string, the middleware
    reads the ``X-Remote-Email`` header set by oauth2-proxy after Keycloak
    authentication and stores a session flag if the email matches.

    The setting is read on every request (in ``__call__``) so that
    ``@override_settings`` works correctly in tests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        val = getattr(settings, 'DOCUMENT_TRANSLATION_ENABLED', False)
        if isinstance(val, str):
            try:
                regex = re.compile(val, re.IGNORECASE)
            except re.error:
                logger.warning(
                    "Invalid DOCUMENT_TRANSLATION_ENABLED regex: %r — "
                    "document translation access will not be granted.",
                    val,
                )
                return self.get_response(request)

            email = request.META.get('HTTP_X_REMOTE_EMAIL')
            if email:
                if regex.search(email):
                    if not request.session.get('document_translations'):
                        request.session['document_translations'] = True
                else:
                    request.session.pop('document_translations', None)

        return self.get_response(request)
