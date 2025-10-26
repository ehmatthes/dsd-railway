Configuration-only deployment (Using SQLite)
---

- Install the [Railway CLI](https://docs.railway.com/guides/cli)
- Choose a name for your deployed project, and use it everywhere you see `<project-name>` Run the following commands:

```sh
$ railway login # May need to use `railway login --browserless`
$ pip install dsd-railway
# Add `django_simple_deploy` to `INSTALLED_APPS`
$ python manage.py deploy --deployed-project-name <project-name> --db sqlite
$ git status
# Review changes
$ git add .
$ git commit -m "Configured for deployment to Railway."
```

- Run the following. (You may see a bunch of errors, or a crashed deployment after `railway up`. Those errors will go away after creating the volume where the database file will be written. This is Railway's [recommended approach](https://docs.railway.com/guides/django#deploy-from-the-cli)!)

```sh
$ railway init --name <project-name>
...
Created project <project-name> on <username>'s Projects
https://railway.com/project/<project-id>>
```

You can get your project's ID from the output. You can also get the project's ID from your dashboard; look under the overall project's *Settings* tab, not the service's *Settings*.

```sh
$ railway up --ci
$ railway variables --set "RAILWAY_RUN_UID=0" --service <project-name> --skip-deploys
$ railway link --project <project-id> --service <project-name>
$ railway volume add --mount-path /app/data
$ railway redeploy
$ railway domain --port 8080 --service <project-name>
```

After this last command, you should see the URL for your project. You may need to wait a few minutes for the deployment to finish.