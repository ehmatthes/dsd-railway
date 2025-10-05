"""Destroy a project on Railway."""

import sys
import os
from pprint import pprint

import requests


project_id = sys.argv[1]

print(f"Destroying project: {project_id}")

confirm = input("\nDestroy project? (y/n): ")
if confirm.lower() not in ("y", "yes"):
    sys.exit()

railway_token = os.environ.get("RAILWAY_API_TOKEN", None)
print(railway_token)
if not railway_token:
    print("Please set the RAILWAY_API_TOKEN environment variable.")
    sys.exit()

base_url = "https://backboard.railway.com/graphql/v2"
headers = {
    "Authorization": f"Bearer {railway_token}",
    "Content-Type": "application/json",
}

payload = {
    "query": "query { me { name email } }"
}

r = requests.post(base_url, headers=headers, json=payload, timeout=30)
data = r.json()

pprint(data)