"""Utils for working with settings for the deployed project."""

from django.utils.safestring import mark_safe

from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config


def get_db_block(templates_path, db):
    """Get DATABASES settings block.
    
    Uses mark_safe(), so block is not escaped by template engine.
    """
    # No need for a conditional block, use --db arg to get correct template
    # for DATABASES block.
    path_db_block = templates_path / f"db_block_{db}.py"
    db_block = path_db_block.read_text()

    if dsd_config.wagtail_project:
        # Wagtail projects don't need indentation.
        return mark_safe(db_block)

    # Non-wagtail projects need an indented settings block.
    # Get lines, indent them all, then remove indentation from first line.
    lines = db_block.splitlines()
    indented_lines = [f"    {l}" if l else l for l in lines]
    indented_block = "\n".join(indented_lines)
    indented_block = indented_block.removeprefix("    ")

    return mark_safe(indented_block)
