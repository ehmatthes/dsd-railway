dsd-railway
===

A plugin for deploying Django projects to Railway, using django-simple-deploy.

For full documentation, see the documentation for [django-simple-deploy](https://django-simple-deploy.readthedocs.io/en/latest/).

Current status
---

This plugin is in a pre-1.0 development phase. It has limited functionality at the moment, but should evolve quickly.

Configuration-only deployment
---

The following instructions set up a Postgres database. If you want to use SQLite instead, see [these instructions](tmp_docs/config_only_sqlite.md).

First, install the [Railway CLI](https://docs.railway.com/guides/cli). Choose a name for your deployed project, and use it everywhere you see `<project-name>`. Run the following commands to configure your project for deployment:

```sh
$ railway login # May need to use `railway login --browserless`
$ pip install dsd-railway
# Add `django_simple_deploy` to `INSTALLED_APPS`
$ python manage.py deploy --deployed-project-name <project-name>
$ git status
# Review changes
$ git add .
$ git commit -m "Configured for deployment to Railway."
```

- Now run the following to actually deploy your project to Railway. (You may see a bunch of errors, or a crashed deployment, after running `railway up`. Those errors will go away after creating the database. This is Railway's [recommended approach](https://docs.railway.com/guides/django#deploy-from-the-cli)!)

```sh
$ railway init --name <project-name>
$ railway up
$ railway add --database postgres
$ railway variables \
    --set 'PGDATABASE=${{Postgres.PGDATABASE}}' \
    --set 'PGUSER=${{Postgres.PGUSER}}' \
    --set 'PGPASSWORD=${{Postgres.PGPASSWORD}}' \
    --set 'PGHOST=${{Postgres.PGHOST}}' \
    --set 'PGPORT=${{Postgres.PGPORT}}' \
    --service <project-name>
$ railway domain --port 8080 --service <project-name>
```

After this last command, you should see the URL for your project. You may need to wait a few minutes for the deployment to finish.

If your deployment doesn't seem to work, you can try redeploying it:

```sh
$ railway redeploy --service <project-name>
```

Fully automated deployment
---

First, install the [Railway CLI](https://docs.railway.com/guides/cli). Then run the following commands:

```sh
$ railway login # You may need to use `railway login --browserless`
$ pip install dsd-railway
# Add django_simple_deploy to INSTALLED_APPS.
$ python manage.py deploy --automate-all
```

Your deployed project should appear in a new browser tab.

### Using SQLite

By default, a Postgres database will be used. If you prefer to use SQLite, include the `--db sqlite` argument when calling `deploy`:

```sh
$ python manage.py deploy --automate-all --db sqlite
```

This will create a persistent [Railway volume](https://docs.railway.com/reference/volumes) where the SQLite database file will be written.

Destroying a project
---

This is mostly for developers, but if you're trying this out and want to destroy a project the following should work:

```sh
$ export RAILWAY_API_TOKEN=<account-token>
$ python developer_resources/destroy_project.py <project-id>
```

Be careful running this command, as it is an immediately destructive action. If you want to be more cautious, you can delete the project in your Railway dashboard. Railway schedules the project for deletion in the next 48 hours, giving you some possibility of restoring the project if you need to.

If you don't know the ID of your project, you can run `railway status --json`. The ID will the first item in the JSON output. You can also find the project ID in the Settings tab of the overall project; make sure you're looking at the project's Settings tab, not the service's Settings.
