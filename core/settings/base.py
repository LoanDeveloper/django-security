import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Load .env if present
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="changeme-in-.env")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "axes",
    "django_htmx",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    # Local apps
    "accounts",
    "catalog",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # django-axes brute force protection
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default=""),
        "PORT": env("DB_PORT", default=""),
    }
}

# Password validation and hashing
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_USER_MODEL = "accounts.User"

# Allow login by username or email plus Axes backend for lockouts
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "accounts.auth_backends.UsernameOrEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise for static files in production-like envs
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 7

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session & CSRF cookie security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"

# Security headers (documented for prod)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 0  # enable >0 in prod settings
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# django-axes configuration (anti-bruteforce)
AXES_ENABLED = True
AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", default=5)
AXES_COOLOFF_TIME = env.int("AXES_COOLOFF_TIME", default=15)  # minutes
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

# Logging to file for auth events
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s %(message)s",
        }
    },
    "handlers": {
        "auth_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "auth.log"),
            "when": "midnight",
            "backupCount": 14,
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security.csrf": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "auth": {"handlers": ["auth_file", "console"], "level": "INFO", "propagate": False},
        "axes.watch_login": {
            "handlers": ["auth_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Django REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "120/minute",
    },
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "TP2 API",
    "DESCRIPTION": "API publique versionnée avec endpoints RGPD.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS (whitelist stricte en dev)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# Throttling DRF (endpoints sensibles)
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] += [
    "rest_framework.throttling.ScopedRateThrottle",
]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "login": "10/minute",
        "password_reset": "10/minute",
        "export": "10/minute",
        "erase": "10/minute",
    }
)
