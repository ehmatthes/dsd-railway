dsd-railway
===

A plugin for deploying Django projects to Railway, using django-simple-deploy.

For full documentation, see the documentation for [django-simple-deploy](https://django-simple-deploy.readthedocs.io/en/latest/).

Current status
---

This plugin is in a pre-1.0 development phase. It has limited functionality at the moment, but should evolve quickly.

Automated deployment
---

- Install the [Railway CLI](https://docs.railway.com/guides/cli)
- Log in, using `railway login`. You may need to run `railway login --browserless`.
- Install `dsd-railway`: `pip install dsd-railway`
- Add `django_simple_deploy` to `INSTALLED_APPS`
- Run `python manage.py deploy --automate-all`.
