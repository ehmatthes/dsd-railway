Changelog: dsd-<platformname>
===

0.2 - Support SQLite

Supports both Postgres and SQLite deployments.

### 0.2.0

#### External changes

- Adds new CLI argument: `--db <postgres|sqlite>` (defaults to `postgres`)
- 

#### Internal changes

- Lots of refactoring, not worth detailing in this pre-1.0 release.

0.1 - Provisional support for deployments
---

### 0.1.3

#### External changes

- More complete user-facing messages.
- Validates CLI.

#### Internal changes

- Checks that cached project ID matches ID from `RAILWAY_PROJECT_ID` in env var before destroying remote e2e test resources.
- Moved work to relevant utils modules.
- Integration test for railway.toml.
- Integration test for staticfiles/placeholder.txt.
- Confirms API token available before running e2e test.
- Ran `black`.

### 0.1.2

#### External changes

- Static files are handled correctly.
- Writes a railway.toml file to run collectstatic on each deploy.
- Clarified documentation.
- Explicitly links project on fully-automated deployments.
- Makes sure environment variables are readable before re-deploying, after building database.
- Use pathlib syntax in settings file.
- Explicitly insert whitenoise middleware after security middleware, rather than hardcoding position.

#### Internal changes

- Implements e2e tests for configuration-only and fully automated modes.

### 0.1.1

#### External changes

- Use local project name instead of hard coded project name.
- README has instructions for current usage.
- Temp docs/ dir.
- Waits for project to be ready before opening in browser.

#### Internal changes

- Script for destroying test projects by project ID.

### 0.1.0

#### External changes

- Supports deployment of the sample blog project using `--automate-all`. Some values are hard-coded.

#### Internal changes

- N/A
