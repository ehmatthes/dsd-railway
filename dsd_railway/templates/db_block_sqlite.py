# Configure a SQLite db.
# See: https://github.com/adamghill/dj-lite
# You can override individual settings in the call to `sqlite_config()`.
# Example: `sqlite_config(BASE_DIR, file_name="production_db.sqlite3")``
from dj_lite import sqlite_config
DATABASES = {
  "default": sqlite_config(BASE_DIR),
}