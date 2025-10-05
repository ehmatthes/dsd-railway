dsd-railway
===

A plugin for deploying Django projects to Railway, using django-simple-deploy.

For full documentation, see the documentation for [django-simple-deploy](https://django-simple-deploy.readthedocs.io/en/latest/).

Current status
---

This plugin is in a pre-1.0 development phase. It has limited functionality at the moment, but should evolve quickly.

Configuration-only deployment
---

- Install the [Railway CLI](https://docs.railway.com/guides/cli)
- Log in, using `railway login`. You may need to run `railway login --browserless`.
- Install `dsd-railway`: `pip install dsd-railway`
- Add `django_simple_deploy` to `INSTALLED_APPS`
- Choose a name for your deployed project, and run `python manage.py deploy --deployed-project-name <project-name>`
- Review and then commit changes.
- Run the following:
```sh
$ railway init --name <project-name>
$ railway up
$ railway add --database postgres
$ railway variables \
    --set "PGDATABASE=${{Postgres.PGDATABASE}}" \
    --set "PGUSER=${{Postgres.PGUSER}}" \
    --set "PGPASSWORD=${{Postgres.PGPASSWORD}}" \
    --set "PGHOST=${{Postgres.PGHOST}}" \
    --set "PGPORT=${{Postgres.PGPORT}}" \
    --service <project-name>
$ railway redeploy --service <project-name> --yes
$ railway domain --port 8080 --service <project-name>
```

After this last command, you should see the URL for your project. You may need to wait a few minutes for the deployment to finish.

Fully automated deployment
---

- Install the [Railway CLI](https://docs.railway.com/guides/cli)
- Log in, using `railway login`. You may need to run `railway login --browserless`.
- Install `dsd-railway`: `pip install dsd-railway`
- Add `django_simple_deploy` to `INSTALLED_APPS`
- Run `python manage.py deploy --automate-all`.

Your deployed project should appear in a new browser tab.

Destroying a project
---

This is mostly for developers, but if you're trying this out and want to destroy a project the following should work:

```sh
$ export RAILWAY_API_TOKEN=<account-token>
$ python developer_resources/destroy_project.py <project-id>
```

Be careful running this command, as it is a destructive action.
