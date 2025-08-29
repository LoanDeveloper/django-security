from .base import *  # noqa

# Production overrides
DEBUG = False

# HSTS enabled in prod
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days


