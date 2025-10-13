"""Helper functions specific to dsd-railway e2e tests."""

import time
import json
import os
from pprint import pprint
import webbrowser

import requests

from tests.e2e_tests.utils import it_helper_functions as it_utils
from tests.e2e_tests.utils.it_helper_functions import make_sp_call


def automate_all_steps(app_name):
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


def config_only_steps(app_name):
    """Carry out steps that users would in the configuration-only workflow."""
    it_utils.commit_configuration_changes()

    cmd = f"railway init --name {app_name}"
    make_sp_call(cmd)

    # Get project ID.
    cmd = "railway status --json"
    output = make_sp_call(cmd, capture_output=True).stdout.decode()
    output_json = json.loads(output)
    project_id = output_json["id"]
    request.config.cache.set("project_id", project_id)

    # Link project.
    cmd = f"railway link --project {project_id} --service {app_name}"
    make_sp_call(cmd)

    cmd = "railway up"
    make_sp_call(cmd)

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
    for _ in range(int(timeout/pause)):
        msg = "  Reading env vars..."
        print(msg)
        cmd = f"railway variables --service {app_name} --json"
        output = make_sp_call(cmd, capture_output=True)
        output_json = json.loads(output.stdout.decode())
        if output_json["PGUSER"] == "postgres":
            break
        
        print(output_json)
        time.sleep(pause)

    cmd = f"railway domain --port 8080 --service {app_name} --json"
    output = make_sp_call(cmd, capture_output=True)

    output_json = json.loads(output.stdout.decode())
    project_url = output_json["domain"]

    # Wait for a 200 response.
    pause = 10
    timeout = 300
    for _ in range(int(timeout/pause)):
        msg = "  Checking if deployment is ready..."
        print(msg)
        r = requests.get(project_url)
        if r.status_code == 200:
            break

        time.sleep(pause)

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
    """Destroy the deployed project, and all remote resources."""
    print("\nCleaning up:")

    # Get cached proejct ID and app_name.
    # DEV: These blocks can be cleaned up with the walrus operator.
    project_id = request.config.cache.get("project_id", None)
    if not project_id:
        print("  No project id found; can't destroy any remote resources.")
        return None
    
    app_name = request.config.cache.get("app_name", None)
    if not app_name:
        print("  No app_name available; can't destroy any remote resources.")
        return None
    
    # Get project ID from env vars, and make sure it matches cached value.
    print("  Checking that project IDs match...")
    cmd = f"railway variables --service {app_name} --json"
    output = make_sp_call(cmd, capture_output=True)
    output_json = json.loads(output.stdout.decode())
    project_id_env_var = output_json["RAILWAY_PROJECT_ID"]
    
    if project_id_env_var == project_id:
        print("    Project IDs match.")
    else:
        msg = f"  Cached project ID:       {project_id}"
        msg += f"\n  Project ID from env var: {project_id_env_var}"
        msg += "\n  Project IDs don't match. Not destroying any remote resources."
        print(msg)
        
        return None

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