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
from pathlib import Path

from django.utils.safestring import mark_safe

import requests

from . import deploy_messages as platform_msgs
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
        pass

    def _prep_automate_all(self):
        """Take any further actions needed if using automate_all."""
        pass



    def _modify_settings(self):
        """Add Railway-specific settings."""
        msg = "\nAdding a Railway-specific settings block."
        plugin_utils.write_output(msg)

        template_path = self.templates_path / "settings.py"
        plugin_utils.modify_settings_file(template_path)

    def _make_static_dir(self):
        """Add a static/ dir if needed."""
        msg = "\nAdding a static/ directory and a placeholder text file."
        plugin_utils.write_output(msg)

        path_static = Path("static")
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

        # Initialize empty project on Railway.
        plugin_utils.write_output("  Initializing empty project on Railway...")
        cmd = "railway init"
        plugin_utils.run_slow_command(cmd)

        # Deploy the project.
        msg = "  Pushing code to Railway."
        msg += "\n  You'll see a database error, which will be addressed in the next step."
        plugin_utils.write_output(msg)
        
        cmd = "railway up"
        plugin_utils.run_slow_command(cmd)

        # Add a database.
        msg = "  Adding a database..."
        plugin_utils.write_output(msg)

        cmd = "railway add"
        output = run_quick_command(cmd)
        plugin_utils.write_output(output, write_to_console=False)

        # Set env vars.
        self._set_env_vars()

        # Redeploy.
        cmd = "railway redeploy"
        plugin_utils.run_slow_command(cmd)

        # Generate a Railway domain.
        msg = "  Generating a Railway domain..."
        cmd = "railway domain --port 8080 --json"
        output = plugin_utils.run_quick_command(cmd)
        breakpoint()

        # Should set self.deployed_url, which will be reported in the success message.
        pass

    def _show_success_message(self):
        """After a successful run, show a message about what to do next.

        Describe ongoing approach of commit, push, migrate.
        """
        if dsd_config.automate_all:
            msg = platform_msgs.success_msg_automate_all(self.deployed_url)
        else:
            msg = platform_msgs.success_msg(log_output=dsd_config.log_output)
        plugin_utils.write_output(msg)

    
    def _set_env_vars(self):
        """Set required environment variables for Railway."""
        msg = "  Setting environment variables on Railway..."
        plugin_utils.write_output(msg)

        env_vars = [
            '--set "PGDATABASE=${{Postgres.PGDATABASE}}"',
            '--set "PGUSER=${{Postgres.PGUSER}}"',
            '--set "PGPASSWORD=${{Postgres.PGPASSWORD}}"',
            '--set "PGHOST=${{Postgres.PGHOST}}"',
            '--set "PGPORT=${{Postgres.PGPORT}}"',
        ]

        cmd = f"railway variables {' '.join(env_vars)}"
        output = plugin_utils.run_quick_command(cmd)
        plugin_utils.write_output(output)
