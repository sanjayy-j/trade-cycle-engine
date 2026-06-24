"""
Production settings.

Used when DJANGO_ENV=production. Fails fast at import time if required
secrets/hosts aren't configured, and enforces HTTPS-only cookies/HSTS.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable must be set when DJANGO_ENV=production."
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS environment variable must be set when DJANGO_ENV=production."
    )

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
