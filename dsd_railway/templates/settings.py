{{current_settings}}

# Railway settings.
import os

if os.environ.get("RAILWAY_PROJECT_NAME", ""):
    DEBUG = False

    # Configure a Postgres db.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("PGDATABASE", ""),
            "USER": os.environ.get("PGUSER", ""),
            "PASSWORD": os.environ.get("PGPASSWORD", ""),
            "HOST": os.environ.get("PGHOST", ""),
            "PORT": os.environ.get("PGPORT", ""),
        }
    }

    # Static files config.
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "staticfiles"

    i = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(i + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

    # Allowed hosts, CSRF.
    ALLOWED_HOSTS = [".up.railway.app"]
    CSRF_TRUSTED_ORIGINS = ["https://*.railway.app"]
