"""Helper functions specific to dsd-railway e2e tests."""

import time
import json
import os
from pprint import pprint
import webbrowser

import requests
import pytest

from tests.e2e_tests.utils import it_helper_functions as it_utils
from tests.e2e_tests.utils.it_helper_functions import make_sp_call


def check_railway_api_token():
    """Make sure api token is available before running e2e test.

    This isn't perfect, because the user is still asked if they want to destroy
    the project by core. That's a bit more work to sort out. This is still better
    than running tests, and then having to manually destroy the test project.
    """
    railway_token = os.environ.get("RAILWAY_API_TOKEN", None)
    if railway_token is None:
        msg = "\nPlease set the RAILWAY_API_TOKEN environment variable and then run this test."
        msg += (
            "\nThe token is needed in order to destroy the test project during cleanup."
        )
        print(msg)

        pytest.exit(msg)


def automate_all_steps(request, app_name):
    """Carry out steps needed to test an --automate-all run."""
    # Get project ID.
    cmd = "railway status --json"
    output = make_sp_call(cmd, capture_output=True).stdout.decode()
    output_json = json.loads(output)
    project_id = output_json["id"]
    request.config.cache.set("project_id", project_id)

    # Get URL
    cmd = f"railway variables --service {app_name} --json"
    output = make_sp_call(cmd, capture_output=True).stdout.decode()
    output_json = json.loads(output)
    return f"https://{output_json['RAILWAY_PUBLIC_DOMAIN']}"


def config_only_steps(request, app_name, cli_options):
    """Carry out steps that users would in the configuration-only workflow."""
    it_utils.commit_configuration_changes()

    # Create an empty remote project.
    cmd = f"railway init --name {app_name}"
    make_sp_call(cmd)
    project_id = _get_project_id(request)

    # Link remote project and service to local repo.
    cmd = f"railway link --project {project_id} --service {app_name}"
    make_sp_call(cmd)

    # Push project to Railway.
    cmd = "railway up"
    make_sp_call(cmd)

    # Build and configure remote database.
    db_arg = _get_db_arg(cli_options)
    if db_arg == "postgres":
        _configure_postgres(app_name)
    elif db_arg == "sqlite":
        _configure_sqlite(project_id, app_name)

    # Get deployed URL, and open project in browser.
    project_url = _get_deployed_url(app_name)
    _ensure_200_response(project_url)
    webbrowser.open(project_url)

    return project_url


def check_log(tmp_proj_dir):
    """Check the log that was generated during a full deployment.

    Checks that log file exists, and that DATABASE_URL is not logged.
    """
    path = tmp_proj_dir / "dsd_logs"
    if not path.exists():
        return False

    log_files = list(path.glob("dsd_*.log"))
    if not log_files:
        return False

    log_str = log_files[0].read_text()
    if "DATABASE_URL" in log_str:
        return False
    return True


def destroy_project(request):
    """Destroy the deployed project, and all remote resources.
    
    This is called by django-simple-deploy's e2e test, after the test
    is finished running.
    """
    print("\nCleaning up:")

    # Get cached proejct ID and app_name.
    if not (project_id := request.config.cache.get("project_id", None)):
        print("  No project id found; can't destroy any remote resources.")
        return

    if not (app_name := request.config.cache.get("app_name", None)):
        print("  No app_name available; can't destroy any remote resources.")
        return

    # Get project ID from env vars, and make sure it matches cached value.
    if _verify_cached_project_id(app_name, project_id):
        _destroy_railway_project(project_id)    


# --- Helper functions ---

def _get_project_id(request):
    """Get ID of the project that was just created."""
    cmd = "railway status --json"
    output = make_sp_call(cmd, capture_output=True).stdout.decode()
    output_json = json.loads(output)
    project_id = output_json["id"]
    request.config.cache.set("project_id", project_id)

    return project_id

def _get_db_arg(cli_options):
    """Parse cli options for --db value."""
    if "--db sqlite" in cli_options.plugin_args_string:
        return "sqlite"
    return "postgres"

def _configure_postgres(app_name):
    """Create and configure the remote Postgres database."""
    cmd = "railway add --database postgres"
    make_sp_call(cmd)

    env_vars = [
        '--set "PGDATABASE=${{Postgres.PGDATABASE}}"',
        '--set "PGUSER=${{Postgres.PGUSER}}"',
        '--set "PGPASSWORD=${{Postgres.PGPASSWORD}}"',
        '--set "PGHOST=${{Postgres.PGHOST}}"',
        '--set "PGPORT=${{Postgres.PGPORT}}"',
    ]
    cmd = f"railway variables {' '.join(env_vars)} --service {app_name}"
    make_sp_call(cmd)

    # Make sure env vars are reading from Postgres values.
    pause = 10
    timeout = 60
    for _ in range(int(timeout / pause)):
        msg = "  Reading env vars..."
        print(msg)
        cmd = f"railway variables --service {app_name} --json"
        output = make_sp_call(cmd, capture_output=True)
        output_json = json.loads(output.stdout.decode())
        if output_json["PGUSER"] == "postgres":
            break

        print(output_json)
        time.sleep(pause)

def _configure_sqlite(project_id, app_name):
    """Create and configure remote SQLite database."""
    cmd = f'railway variables --set "RAILWAY_RUN_UID=0" --service blog --skip-deploys'
    make_sp_call(cmd)

    # Link project right before creating volume..
    cmd = f"railway link --project {project_id} --service {app_name}"
    make_sp_call(cmd)

    cmd = "railway volume add --mount-path /app/data"
    make_sp_call(cmd)

    cmd = "railway redeploy --yes"
    make_sp_call(cmd)

def _get_deployed_url(app_name):
    """Get the URL of the deployed project."""
    cmd = f"railway domain --port 8080 --service {app_name} --json"
    output = make_sp_call(cmd, capture_output=True)

    output_json = json.loads(output.stdout.decode())
    return output_json["domain"]

def _ensure_200_response(project_url):
    """Wait for a 200 response from the deployed project."""
    pause = 10
    timeout = 300
    for _ in range(int(timeout / pause)):
        msg = "  Checking if deployment is ready..."
        print(msg)
        r = requests.get(project_url)
        if r.status_code == 200:
            break

        time.sleep(pause)

def _destroy_railway_project(project_id):
    """Carry out the actual deletion."""
    print("  Destroying Railway project...")
    railway_token = os.environ.get("RAILWAY_API_TOKEN", None)
    if not railway_token:
        print("Please set the RAILWAY_API_TOKEN environment variable.")
        return

    base_url = "https://backboard.railway.com/graphql/v2"
    headers = {
        "Authorization": f"Bearer {railway_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": f'mutation projectDelete {{ projectDelete(id: "{project_id}")}}'
    }

    r = requests.post(base_url, headers=headers, json=payload, timeout=30)
    data = r.json()
    pprint(data)

def _verify_cached_project_id(app_name, project_id):
    """Get project ID from env vars, and make sure it matches cached value."""
    print("  Checking that project IDs match...")
    cmd = f"railway variables --service {app_name} --json"
    output = make_sp_call(cmd, capture_output=True)
    output_json = json.loads(output.stdout.decode())
    project_id_env_var = output_json["RAILWAY_PROJECT_ID"]

    if project_id_env_var == project_id:
        print("    Project IDs match.")
        return True

    msg = f"  Cached project ID:       {project_id}"
    msg += f"\n  Project ID from env var: {project_id_env_var}"
    msg += "\n  Project IDs don't match. Not destroying any remote resources."
    print(msg)
    return False