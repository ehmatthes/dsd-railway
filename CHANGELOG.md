Changelog: dsd-<platformname>
===

0.1 - Provisional support for deployments
---

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
