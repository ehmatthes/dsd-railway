"""Integration tests focusing on an SQLite deployment."""

import sys
from pathlib import Path
import subprocess

import pytest

from tests.integration_tests.utils import it_helper_functions as hf
from tests.integration_tests.utils import manage_sample_project as msp
from tests.integration_tests.conftest import (
    tmp_project,
    run_dsd,
    reset_test_project,
    pkg_manager,
    dsd_version,
)

# Skip the default module-level `manage.py deploy call`, so we can call
# `deploy` with our own set of plugin-specific CLI args.
pytestmark = pytest.mark.skip_auto_dsd_call

# --- Fixtures ---


# --- Test modifications to project files. ---


def test_settings(tmp_project):
    """Verify there's a Railway-specific settings section.
    This function only checks the entire settings file. It does not examine
      individual settings.

    Note: This will fail as soon as you make updates to the user's settings file.
    That's good! Look in the test's temp dir, look at the settings file after it was
    modified, and if it's correct, copy that file to reference_files. Tests should pass
    again.
    """

    # DEV: Can this be autouse for the module?
    cmd = "python manage.py deploy --db sqlite"
    stdout, stderr = msp.call_deploy(tmp_project, cmd)

    hf.check_reference_file(tmp_project, "blog/settings.py", "dsd-railway", reference_filename="settings_sqlite.py")


def test_requirements_txt(tmp_project, pkg_manager, tmp_path, dsd_version):
    """Test that the requirements.txt file is correct.
    Note: This will fail as soon as you add new requirements. That's good! Look in the
    test's temp dir, look at the requirements.txt file after it was modified, and if
    it's correct, copy it to reference files. Tests should pass again.
    """
    # DEV: Can this be autouse for the module?
    cmd = "python manage.py deploy --db sqlite"
    stdout, stderr = msp.call_deploy(tmp_project, cmd)

    if pkg_manager == "req_txt":
        context = {"current-version": dsd_version}
        hf.check_reference_file(
            tmp_project,
            "requirements.txt",
            "dsd-railway",
            context=context,
            tmp_path=tmp_path,
            reference_filename="requirements_sqlite.txt",
        )
    elif pkg_manager in ["poetry", "pipenv"]:
        assert not Path("requirements.txt").exists()