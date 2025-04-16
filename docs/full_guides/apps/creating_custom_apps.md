## Django Apps vs. Simmate Apps

Simmate is built on top of the [Django web framework](https://www.djangoproject.com/), which is used by thousands of developers to build a countless number of applications and software. In turn, the applications built with Django support millions of users accross the globe. Moreover, many major software companies & products were built using Django:

- [Instagram](https://www.instagram.com/)
- [Spotify](https://open.spotify.com/)
- [Pinterest](https://www.pinterest.com/)
- [Dropbox](https://www.dropbox.com/)
- [The Washington Post](https://www.washingtonpost.com/)
- ... and many more!

And again, Simmate is a small addition to this list. 

With this in mind, it is helpful to know that all of our Simmate apps are really just Django apps -- but with some extra features tacked on (e.g. chemistry tools & workflows). In fact, **any app you build with Django can be used with Simmate.** Because of this, we highly recommend exploring [Django's guides](https://docs.djangoproject.com/en/5.2/) to get started.


## Step-by-Step Tutorials

1. [Django's official tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
2. [Simmate's getting-start guide](/getting_started/custom_tables_and_apps/create_a_custom_app.md)

!!! note
    `django` is installed for you when you install `simmate`, so you can start their tutorials without any additional setup.

## Folder Structure

All apps follow the same folder structure, where every folder is optional (and in practice, most apps only contain a few of these folders):

```
├── example_app
│   ├── configuration
│   ├── command_line
│   ├── inputs
│   ├── outputs
│   ├── error_handlers
│   ├── migrations
│   ├── models
│   ├── schedules
│   ├── templates
│   ├── urls
│   ├── views
│   └── workflows
```

There are no restrictions on adding extra python modules to your app. In fact, some of our apps include extra functionality, such as utilities or toolkit add-ons.


## Generate Example App Files

1. To start a new app, navigate to your desired folder for code storage and run:
``` bash
simmate create-app
```

2. You will then see a new folder named `my_new_project`:
```
my_new_project/
├── pyproject.toml
├── README.md
└── example_app
    ├── __init__.py
    ├── apps.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    └── workflows.py
```

3. Edit the files to start building out your new app

!!! tip
    Once you get the hang of building apps, all of the code in these files will be annoying to go through & delete. There's nothing wrong with building your app out one file at a time, and ingoring the `simmate create-app` command.


## Register Your App

Add your app's config to Simmate's list of registered apps:

``` bash
simmate config add 'example_app.apps.ExampleAppConfig'
```

!!! note
    For Django users, all Simmate is doing here is adding your config to Simmate's internal list of [Django `INSTALLED_APPS`](https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-INSTALLED_APPS)


## Adding Tables

Add any `Database` table (or django `Model`) to the app's `models.py` file. If you make a models folder instead (`my_app/models`), make sure your final tables are imported within `my_app/models/__init__.py`.

``` python
# in `my_app/models/__init__.py`
from .structures import MyStructureTable
from .test_results import MyTestResults
```

!!! note
    Simmate uses [Django](https://docs.djangoproject.com/en/5.2/topics/db/models/) to detect and maintain models, so all the same rules apply.

## Adding Workflows

Add any `Workflow` to the app's `workflows.py` file AND list them in the `__all__` global variable.:
``` python
# in workflows.py
__all__ = [
    "MyExample__Workflow__Test123",
    "MyExample__Workflow__Test321",
]

# (then these workflows are defined)
```

If you make `my_app/workflows` a folder, make sure your final tables are imported within `my_app/workflows/__init__.py`
``` python
# in `my_app/workflows/__init__.py`
from .flow_abc import MyExample__Workflow__TestABC
from .flow_def import MyExample__Workflow__TestDEF
```


## Adding Web UI (urls/views)

Normally in Django, you need to add `include('example_app.urls')` and define what url endpoints this will map to. Simmate automatically handles this when you build `urls.py` and `views.py` files. Everything in your `urls.py` will be mapped to a namespace matching your app's name.

For example, if you app was called `example_app` and this was your `urls.py`:

``` python
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('my-custom-view/', views.my_custom_view, name='custom'),
]
```

You could view them in the Simmate website at:

- `http://127.0.0.1:8000/apps/example_app/`
- `http://127.0.0.1:8000/apps/example_app/my-custom-view/`
