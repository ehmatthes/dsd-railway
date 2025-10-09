"""Helper functions for interactions with the Railway server."""

from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config


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
