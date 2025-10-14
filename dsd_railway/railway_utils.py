"""Helper functions for interactions with the Railway server."""

import json
import subprocess
import time

import requests

from .plugin_config import plugin_config
from . import deploy_messages as platform_msgs

from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config
from django_simple_deploy.management.commands.utils.command_errors import (
    DSDCommandError,
)


def validate_cli():
    """Make sure CLI is installed, and user is authenticated."""
    cmd = "railway whoami"

    # Generates a FileNotFoundError on macOS and Ubuntu if CLI not installed.
    try:
        output_obj = plugin_utils.run_quick_command(cmd)
    except FileNotFoundError:
        raise DSDCommandError(platform_msgs.cli_not_installed)

    plugin_utils.log_info(output_obj)
    stdout = output_obj.stdout.decode()
    stderr = output_obj.stderr.decode()

    if "Logged in as " in stdout:
        return

    if "Unauthorized. Please login" in stderr:
        raise DSDCommandError(platform_msgs.cli_logged_out)

    # No logged in or unauthorized message. Don't try to use CLI.
    msg = "Output of `railway whomai` unrecognized. Do you have the CLI installed?"
    raise DSDCommandError(msg)


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

    if plugin_config.db == "postgres":
        add_postgres_db()


def add_postgres_db():
    """Add a Postgres database to the project."""
    msg = "  Adding a Postgres database..."
    plugin_utils.write_output(msg)

    # Add db.
    cmd = "railway add --database postgres"
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)

    # Set required env vars, and make sure they're readable.
    set_postgres_env_vars()
    ensure_pg_env_vars()


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
    plugin_utils.write_output(
        "  Setting DJANGO_SETTINGS_MODULE environment variable..."
    )

    # Need form mysite.settings.production
    dotted_settings_path = ".".join(dsd_config.settings_path.parts[-3:]).removesuffix(
        ".py"
    )

    cmd = f'railway variables --set "DJANGO_SETTINGS_MODULE={dotted_settings_path}" --service {dsd_config.deployed_project_name}'
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)


def ensure_pg_env_vars():
    """Make sure the Postgres environment variables are active.

    Django settings will be incorrect if the environment variables for the app
    are not yet referencing the database config. Make sure the references are
    active before proceeding.
    """
    pause = 10
    timeout = 60
    for _ in range(int(timeout / pause)):
        msg = "  Reading env vars..."
        plugin_utils.write_output(msg)

        cmd = f"railway variables --service {dsd_config.deployed_project_name} --json"
        output = plugin_utils.run_quick_command(cmd)
        plugin_utils.write_output(output)

        output_json = json.loads(output.stdout.decode())
        if output_json["PGUSER"] == "postgres":
            break

        time.sleep(pause)


def redeploy_project():
    """Redeploy the project, usually after env vars have become active."""
    cmd = f"railway redeploy --service {dsd_config.deployed_project_name} --yes"
    output = plugin_utils.run_quick_command(cmd)
    plugin_utils.write_output(output)


def generate_domain():
    """Generate a Railway domain for the project."""
    msg = "  Generating a Railway domain..."
    plugin_utils.write_output(msg)

    cmd = f"railway domain --port 8080 --service {dsd_config.deployed_project_name} --json"
    output = plugin_utils.run_quick_command(cmd)

    output_json = json.loads(output.stdout.decode())
    return output_json["domain"]


def check_status_200(url):
    """Wait for a 200 status from a freshly-deployed project."""
    pause = 10
    timeout = 300
    for _ in range(int(timeout / pause)):
        msg = "  Checking if deployment is ready..."
        plugin_utils.write_output(msg)

        r = requests.get(url)
        if r.status_code == 200:
            msg = "  200 status returned."
            plugin_utils.write_output(msg)
            break

        time.sleep(pause)
