## Django Apps vs. Simmate Apps

Simmate is built on top of the [Django web framework](https://www.djangoproject.com/), which is used by thousands of developers. In fact, many major software companies & products were built using Django:

- [Instagram](https://www.instagram.com/)
- [Spotify](https://open.spotify.com/)
- [Pinterest](https://www.pinterest.com/)
- [Dropbox](https://www.dropbox.com/)
- [The Washington Post](https://www.washingtonpost.com/)

... and many more. Simmate is a very small addition to this list. 

With this in mind, it is helpful to know that all of our Simmate apps are really just Django apps -- but with some extra features tacked on (e.g. chemistry tools & workflows). In fact, **any app you build with Django can be used with Simmate.** Because of this, we highly recommend exploring [Django's intro guides](https://docs.djangoproject.com/en/5.2/intro/) to get started.


## Step-by-Step Tutorials

1. [Django's official tutorial](https://docs.djangoproject.com/en/5.2/intro/)
2. [Simmate's getting-start guide](/getting_started/custom_tables_and_apps/create_a_custom_app.md)

!!! tip
    `django` is installed for you when you install `simmate`, so you can start their tutorials without any additional setup.

## Folder Structure

All apps follow the same folder structure. While almost every folder is optional, we recommend using sub-folders (packages) for `models` and `workflows` once your app grows:

```
├── example_app
│   ├── command_line/    # custom CLI commands
│   ├── components/      # HTMX/UI components
│   ├── migrations/      # Database migrations
│   ├── models/          # Database tables
│   │   ├── __init__.py
│   │   ├── table_1.py
│   │   └── table_2.py
│   ├── schedules/       # periodic/timed tasks
│   ├── templates/       # HTML files
│   ├── workflows/       # Automated tasks
│   │   ├── __init__.py
│   │   ├── flow_1.py
│   │   └── flow_2.py
│   ├── config.py        # App configuration
│   ├── urls.py          # URL routing
│   └── views.py          # Web views
```

There are no restrictions on adding extra python modules to your app. In fact, some of our apps include extra functionality, such as `inputs`, `outputs`, or `error_handlers`.


## Generate Example App Files

1. To start a new app, navigate to your desired folder for code storage and run:
``` bash
simmate start-project
```

2. You will then see a new folder named `my_simmate_project`:
```
my_simmate_project/
├── pyproject.toml
├── README.md
└── example_app
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    └── workflows.py
```

3. Edit the files to start building out your new app

!!! tip
    Once you get the hang of building apps, all of the code in these files will be annoying to go through & delete. There's nothing wrong with building your app out one file at a time, and ingoring the `simmate start-project` command.


## Register Your App

Add your app's config to Simmate's list of registered apps:

``` bash
simmate config add 'example_app.config.ExampleAppConfig'
```

!!! note
    For Django users, all Simmate is doing here is adding your config to Simmate's internal list of [Django `INSTALLED_APPS`](https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-INSTALLED_APPS)


## Adding Tables

You can add database tables (Django `Models`) to your app in two ways:

1.  **A single file:** Add your models directly to `models.py`.
2.  **A folder:** Create a `models/` folder with an `__init__.py` and several sub-modules (e.g., `structures.py`, `results.py`).

If you use a folder, you **must** import your tables into `models/__init__.py` so Simmate can find them:

``` python
# in `my_app/models/__init__.py`
from .structures import MyStructureTable
from .results import MyTestResults
```

!!! note
    Simmate uses the [Django ORM](https://docs.djangoproject.com/en/5.2/topics/db/models/) to manage database tables, so all standard Django model rules apply.
    
!!! tip
    Learn more about defining tables in our [Database guides](/full_guides/database/custom_tables.md).

## Adding Workflows

Similarly, you can organize your workflows as a single file or a folder:

1.  **A single file:** Add workflows to `workflows.py` and list them in the `__all__` variable.
2.  **A folder:** Create a `workflows/` folder with an `__init__.py` and several sub-modules.

If you use a folder, import your workflows into `workflows/__init__.py`:

``` python
# in `my_app/workflows/__init__.py`
from .relaxation import Relaxation__Vasp__MyCustom
from .static_energy import StaticEnergy__Vasp__MyCustom
```

!!! tip
    Read more about building custom workflows in our [Workflow guides](/full_guides/workflows/creating_basic_workflows.md).


## Adding Web UI (urls/views)

Build your `urls.py`, `views.py`, and `templates/` files following [official Django docs](https://docs.djangoproject.com/en/5.2/). 

We recommend following Django's best practice of namespacing your templates within a subfolder named after your app (e.g. `my_app/templates/my_app/home.html`). You should also extend Simmate's base template to get the standard styling and navbar:

```html+django
{% extends "core_components/site_base.html" %}

{% block body %}
    <h1>Hello from My App!</h1>
{% endblock %}
```

Everything in your `urls.py` will be automatically mapped to a namespace matching your app's name. For example, if your app was called `example_app` and this was your `urls.py`:

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

!!! tip
    Read more about custom views in our [Website guides](/full_guides/website/creating_views.md)
