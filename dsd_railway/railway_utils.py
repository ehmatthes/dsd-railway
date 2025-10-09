"""Helper functions for interactions with the Railway server."""

import json
import subprocess

from .plugin_config import plugin_config

from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config


def create_project():
    """Create a new project on Railway."""
    plugin_utils.write_output("  Initializing empty project on Railway...")
    cmd = f"railway init --name {dsd_config.deployed_project_name}"
    plugin_utils.run_slow_command(cmd)

def get_project_id():
    """Get the ID of the remote Railway project."""
    msg = "  Getting project ID..."
    plugin_utils.write_output(msg)

    cmd = "railway status --json"
    output = plugin_utils.run_quick_command(cmd)
    output_json = json.loads(output.stdout.decode())
    plugin_config.project_id = output_json["id"]

    msg = f"  Project ID: {plugin_config.project_id}"
    plugin_utils.write_output(msg)

def link_project():
    """Link the local project to the remote Railway project."""
    msg = "  Linking project..."
    plugin_utils.write_output(msg)
    cmd = f"railway link --project {plugin_config.project_id} --service {dsd_config.deployed_project_name}"

    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)

def push_project():
    """Push a local project to a remote Railway project."""
    msg = "  Pushing code to Railway."
    msg += "\n  You'll see a database error, which will be addressed in the next step."
    plugin_utils.write_output(msg)
    
    cmd = "railway up"
    try:
        plugin_utils.run_slow_command(cmd)
    except subprocess.CalledProcessError:
        msg = "  Expected error, because no Postgres database exists yet. Continuing deployment."
        plugin_utils.write_output(msg)

def add_database():
    """Add a database to the project."""
    msg = "  Adding a database..."
    plugin_utils.write_output(msg)

    cmd = "railway add --database postgres"
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)

def set_postgres_env_vars():
    """Set env vars required to configure Postgres."""
    msg = "  Setting Postgres env vars..."
    plugin_utils.write_output(msg)

    env_vars = [
        '--set "PGDATABASE=${{Postgres.PGDATABASE}}"',
        '--set "PGUSER=${{Postgres.PGUSER}}"',
        '--set "PGPASSWORD=${{Postgres.PGPASSWORD}}"',
        '--set "PGHOST=${{Postgres.PGHOST}}"',
        '--set "PGPORT=${{Postgres.PGPORT}}"',
    ]

    cmd = f"railway variables {' '.join(env_vars)} --service {dsd_config.deployed_project_name} --skip-deploys"
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)

def set_wagtail_env_vars():
    """Set env vars required by most Wagtail projects."""
    plugin_utils.write_output("  Setting DJANGO_SETTINGS_MODULE environment variable...")

    # Need form mysite.settings.production
    dotted_settings_path = ".".join(dsd_config.settings_path.parts[-3:]).removesuffix(".py")

    cmd = f'railway variables --set "DJANGO_SETTINGS_MODULE={dotted_settings_path}" --service {dsd_config.deployed_project_name}'
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)