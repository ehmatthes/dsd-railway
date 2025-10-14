"""Utils for working with settings for the deployed project."""

from django.utils.safestring import mark_safe

from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config


def get_db_block(templates_path, db):
    """Get DATABASES settings block."""
    # No need for a conditional block, use --db arg to get correct template
    # for DATABASES block.
    path_db_block = templates_path / f"db_block_{db}.py"
    db_block = path_db_block.read_text()

    if not dsd_config.settings_path.parts[-2:] == ("settings", "production.py"):
        # Non-wagtail projects need an indented settings block.
        db_block = db_block.replace("\n", "\n    ")

    # Mark safe, so block is not escaped by template engine.
    return mark_safe(db_block)