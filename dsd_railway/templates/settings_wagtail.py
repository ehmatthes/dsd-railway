{{current_settings}}

# Railway settings.
import os

DEBUG = False

# Configure a Postgres db.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("PGDATABASE", ""),
        'USER': os.environ.get("PGUSER", ""),
        'PASSWORD': os.environ.get("PGPASSWORD", ""),
        'HOST': os.environ.get("PGHOST", ""),
        'PORT': os.environ.get("PGPORT", ""),
    }
}

# Static files config.
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Allowed hosts, CSRF.
ALLOWED_HOSTS = [".up.railway.app"]
CSRF_TRUSTED_ORIGINS = ['https://*.railway.app']
