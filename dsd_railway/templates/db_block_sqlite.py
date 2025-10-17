# Configure a SQLite db.
# See: https://github.com/adamghill/dj-lite
# You can override individual settings in the call to `sqlite_config()`.
# Example: `sqlite_config(BASE_DIR, file_name="production_db.sqlite3")``
from dj_lite import sqlite_config
path_data = Path("data")
DATABASES = {
    "default": sqlite_config(base_dir=path_data),
}