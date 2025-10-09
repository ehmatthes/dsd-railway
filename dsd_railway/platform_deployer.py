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
        """Finish automating the push to Railway."""
        # Making this check here lets deploy() be cleaner.
        if not dsd_config.automate_all:
            return

        plugin_utils.commit_changes()

        railway_utils.create_project()
        railway_utils.get_project_id()
        railway_utils.link_project()
        railway_utils.push_project()
        railway_utils.add_database()
        railway_utils.set_postgres_env_vars()

        # Wagtail projects need an env var pointing to the settings module.
        # DEV: This will be `if dsd_config.wagtail_project` shortly.
        if dsd_config.settings_path.parts[-2:] == ("settings", "production.py"):
            railway_utils.set_wagtail_env_vars()

        railway_utils.ensure_pg_env_vars()
        railway_utils.redeploy_project()

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
