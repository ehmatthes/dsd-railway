"""Manages all Railway-specific aspects of the deployment process.

Notes:

Add a new file to the user's project, using a template:

    def _add_dockerfile(self):
        # Add a minimal dockerfile.
        template_path = self.templates_path / "dockerfile_example"
        context = {
            "django_project_name": dsd_config.local_project_name,
        }
        contents = plugin_utils.get_template_string(template_path, context)
"""

import sys, os, re, json
import subprocess
import time
import webbrowser
from pathlib import Path

from django.utils.safestring import mark_safe

import requests

from . import deploy_messages as platform_msgs
from . import railway_utils
from .plugin_config import plugin_config

from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config
from django_simple_deploy.management.commands.utils.command_errors import (
    DSDCommandError,
)


class PlatformDeployer:
    """Perform the initial deployment to Railway

    If --automate-all is used, carry out an actual deployment.
    If not, do all configuration work so the user only has to commit changes, and ...
    """

    def __init__(self):
        self.templates_path = Path(__file__).parent / "templates"

    # --- Public methods ---

    def deploy(self, *args, **options):
        """Coordinate the overall configuration and deployment."""
        plugin_utils.write_output("\nConfiguring project for deployment to Railway...")

        self._validate_platform()
        self._prep_automate_all()

        # Configure project for deployment to Railway
        self._modify_settings()
        self._add_railway_toml()
        self._make_static_dir()
        self._add_requirements()

        self._conclude_automate_all()
        self._show_success_message()

    # --- Helper methods for deploy() ---

    def _validate_platform(self):
        """Make sure the local environment and project supports deployment to Railway.

        Returns:
            None
        Raises:
            DSDCommandError: If we find any reason deployment won't work.
        """
        # Use local project name for deployed project, if no custom name passed.
        if not dsd_config.deployed_project_name:
            dsd_config.deployed_project_name = dsd_config.local_project_name

    def _prep_automate_all(self):
        """Take any further actions needed if using automate_all."""
        pass



    def _modify_settings(self):
        """Add Railway-specific settings."""
        msg = "\nAdding a Railway-specific settings block."
        plugin_utils.write_output(msg)

        if dsd_config.settings_path.parts[-2:] == ("settings", "production.py"):
            template_path = self.templates_path / "settings_wagtail.py"
        else:
            template_path = self.templates_path / "settings.py"

        plugin_utils.modify_settings_file(template_path)

    def _add_railway_toml(self):
        """Add a railway.toml file."""
        msg = "\nAdding a railway.toml file..."
        plugin_utils.write_output(msg)

        template_path = self.templates_path / "railway.toml"
        context = {
            "local_project_name": dsd_config.local_project_name,
        }
        contents = plugin_utils.get_template_string(template_path, context)

        # Write file to project.
        path = dsd_config.project_root / "railway.toml"
        plugin_utils.add_file(path, contents)

    def _make_static_dir(self):
        """Add a static/ dir if needed."""
        msg = "\nAdding a static/ directory and a placeholder text file."
        plugin_utils.write_output(msg)

        path_static = Path("staticfiles")
        plugin_utils.add_dir(path_static)

        # Write a placeholder file, to be picked up by Git.
        path_placeholder = path_static / "placeholder.txt"
        contents = "Placeholder file, to be picked up by Git.\n"
        plugin_utils.add_file(path_placeholder, contents)

    def _add_requirements(self):
        """Add requirements for deploying to Railway."""
        requirements = [
            "gunicorn",
            "whitenoise",
            "psycopg",
            "psycopg-binary",
            "psycopg-pool",
        ]
        plugin_utils.add_packages(requirements)

    def _conclude_automate_all(self):
        """Finish automating the push to Railway.

        - Commit all changes.
        - ...
        """
        # Making this check here lets deploy() be cleaner.
        if not dsd_config.automate_all:
            return

        plugin_utils.commit_changes()

        railway_utils.create_project()
        

        # Get project ID.
        msg = "  Getting project ID..."
        plugin_utils.write_output(msg)
        cmd = "railway status --json"
        output = plugin_utils.run_quick_command(cmd)

        output_json = json.loads(output.stdout.decode())
        plugin_config.project_id = output_json["id"]

        msg = f"  Project ID: {plugin_config.project_id}"
        plugin_utils.write_output(msg)

        # Link project.
        msg = "  Linking project..."
        plugin_utils.write_output(msg)
        cmd = f"railway link --project {plugin_config.project_id} --service {dsd_config.deployed_project_name}"

        output = plugin_utils.run_quick_command(cmd)
        plugin_utils.write_output(output)

        # Deploy the project.
        msg = "  Pushing code to Railway."
        msg += "\n  You'll see a database error, which will be addressed in the next step."
        plugin_utils.write_output(msg)
        
        cmd = "railway up"
        try:
            plugin_utils.run_slow_command(cmd)
        except subprocess.CalledProcessError:
            msg = "  Expected error, because no Postgres database exists yet. Continuing deployment."
            plugin_utils.write_output(msg)

        # Add a database.
        msg = "  Adding a database..."
        plugin_utils.write_output(msg)

        cmd = "railway add --database postgres"
        output = plugin_utils.run_quick_command(cmd)
        plugin_utils.write_output(output)

        # Set env vars.
        self._set_env_vars()

        # Make sure env vars are reading from Postgres values.
        pause = 10
        timeout = 60
        for _ in range(int(timeout/pause)):
            msg = "  Reading env vars..."
            plugin_utils.write_output(msg)
            cmd = f"railway variables --service {dsd_config.deployed_project_name} --json"
            output = plugin_utils.run_quick_command(cmd)
            plugin_utils.write_output(output)

            output_json = json.loads(output.stdout.decode())
            if output_json["PGUSER"] == "postgres":
                break
            
            time.sleep(pause)

        # Redeploy.
        cmd = f"railway redeploy --service {dsd_config.deployed_project_name} --yes"
        output = plugin_utils.run_quick_command(cmd)
        plugin_utils.write_output(output)

        # Generate a Railway domain.
        msg = "  Generating a Railway domain..."
        plugin_utils.write_output(msg)
        cmd = f"railway domain --port 8080 --service {dsd_config.deployed_project_name} --json"
        output = plugin_utils.run_quick_command(cmd)

        output_json = json.loads(output.stdout.decode())
        self.deployed_url = output_json["domain"]

        # Wait {pause} before opening.
        pause = 20
        msg = f"  Waiting {pause}s for deployment to finish..."
        plugin_utils.write_output(msg)

        # Wait for a 200 response.
        pause = 10
        timeout = 300
        for _ in range(int(timeout/pause)):
            msg = "  Checking if deployment is ready..."
            plugin_utils.write_output(msg)
            r = requests.get(self.deployed_url)
            if r.status_code == 200:
                break

            time.sleep(pause)

        webbrowser.open(self.deployed_url)


    def _show_success_message(self):
        """After a successful run, show a message about what to do next.

        Describe ongoing approach of commit, push, migrate.
        """
        if dsd_config.automate_all:
            msg = platform_msgs.success_msg_automate_all(self.deployed_url, plugin_config.project_id)
        else:
            msg = platform_msgs.success_msg(log_output=dsd_config.log_output)
        plugin_utils.write_output(msg)

    
    def _set_env_vars(self):
        """Set required environment variables for Railway."""
        msg = "  Setting environment variables on Railway..."
        plugin_utils.write_output(msg)

        # Configure for Postgres by default.
        railway_utils.set_postgres_env_vars()

        # Wagtail projects need an env var pointing to the settings module.
        if dsd_config.settings_path.parts[-2:] == ("settings", "production.py"):
            railway_utils.set_wagtail_env_vars()
