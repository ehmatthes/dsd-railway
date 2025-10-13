"""Test invalid CLI args."""

from pathlib import Path

import pytest

from tests.integration_tests.conftest import tmp_project
from tests.integration_tests.utils import manage_sample_project as msp

# Skip the default module-level `manage.py deploy call`, so we can call
# `deploy` with our own set of plugin-specific CLI args.
pytestmark = pytest.mark.skip_auto_dsd_call


def test_invalid_db_arg(tmp_project, request):
    """Test an invalid value for the --db arg."""
    cmd = "python manage.py deploy --db mysql"
    stdout, stderr = msp.call_deploy(tmp_project, cmd)

    expected_msg = "DSDCommandError: The value for --db must be either `postgres` or `sqlite`."
    assert expected_msg in stderr
