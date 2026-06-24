"""
Local development settings.

Used automatically unless DJANGO_ENV=production is set. Relaxes the
security settings that would otherwise block plain-HTTP local testing,
and supplies convenient defaults so a fresh checkout works without a
fully populated .env file.
"""

import os

from .base import *  # noqa: F401,F403

if os.getenv("DEBUG") is None:
    DEBUG = True

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

LOGGING["loggers"]["exchange"]["level"] = "DEBUG"
