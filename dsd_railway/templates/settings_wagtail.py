{{current_settings}}

# Railway settings.
import os

DEBUG = False

{{database_block}}

# Static files config.
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Allowed hosts, CSRF.
ALLOWED_HOSTS = [".up.railway.app"]
CSRF_TRUSTED_ORIGINS = ["https://*.railway.app"]
