from .base import *  # noqa

# Development overrides
DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

ALLOWED_HOSTS = ["*"]

# Email backend (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Option: requiert confirmation email à l'inscription
REQUIRE_EMAIL_CONFIRM = True


