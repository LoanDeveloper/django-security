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

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]
