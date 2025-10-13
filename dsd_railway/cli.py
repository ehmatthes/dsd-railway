"""Extends the core django-simple-deploy CLI."""

import json
import shlex
import subprocess

from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config
from django_simple_deploy.management.commands.utils.command_errors import (
    DSDCommandError,
)

from .plugin_config import plugin_config


class PluginCLI:

    def __init__(self, parser):
        """Add plugin-specific args."""
        group_desc = "Plugin-specific CLI args for dsd-railway"
        plugin_group = parser.add_argument_group(
            title="Options for dsd-railway",
            description=group_desc,
        )

        plugin_group.add_argument(
            "--db",
            type=str,
            help="What kind of database? postgres (default) | sqlite",
            default="postgres",
        )


def validate_cli(options):
    """Validate options that were passed to CLI."""
    db = options["db"]
    _validate_db(db)


# --- Helper functions ---

def _validate_db(db):
    """Validate the db arg that was passed."""
    if db not in ("postgres", "sqlite"):
        msg = "The value for --db must be either `postgres` or `sqlite`."
        raise DSDCommandError(msg)
    
    # Valid argument.
    plugin_config.db = db
