# Create a Custom App

Simmate is designed to be extensible. By creating a **Simmate App**, you can organize your research into a reusable package that includes custom database tables, workflows, and even website interfaces.

-------------------------------------------------------------------------------

## Why create an App?

A custom Simmate app gives you several powerful features:

- [x] **Database Integration:** Store workflow results in custom tables.
- [x] **Web Interface:** Access and run your workflows through the Simmate website.
- [x] **Organization:** Keep your code organized as your project grows.
- [x] **Shareability:** Easily share your workflows and data structures with colleagues.
- [x] **Reproducibility:** Package your research code for publication.

-------------------------------------------------------------------------------

## Starting a New Project

To start a new app, navigate to a folder where you want to keep your code and run:

``` bash
simmate start-project
```

This will create a new folder named `my_new_project`. Inside, you'll find a standardized structure:

``` text
my_new_project/
├── pyproject.toml      # Installation instructions
├── README.md           # Project description
└── example_app/        # Your actual code lives here
    ├── __init__.py
    ├── apps.py         # App configuration
    ├── models.py       # Database tables
    ├── workflows.py    # Custom workflows
    ├── urls.py         # Web routes (optional)
    └── views.py        # Web pages (optional)
```

-------------------------------------------------------------------------------

## Naming Your App

!!! danger "Choose carefully"
    Renaming your app later can be difficult because it changes how your code is imported. Choose a name you are happy with from the start.

### 1. Rename the Project Folder
Rename the outer `my_new_project` folder to something relevant to your research (e.g., `warren_lab` or `high_throughput_oxides`). Use lowercase and underscores.

### 2. Update `pyproject.toml`
Open `pyproject.toml` and update the project name:

``` toml
[project]
name = "warren_lab"  # <--- Update this
```

### 3. Rename the App Folder
Rename the inner `example_app` folder to your desired Python package name (e.g., `warren_app`).

### 4. Update `apps.py`
Open `warren_app/apps.py` and update the class name and `name` attribute to match:

``` python
from django.apps import AppConfig

class WarrenAppConfig(AppConfig):  # <--- Update class name
    name = "warren_app"            # <--- Update app name
    verbose_name = "Warren Lab"    # Name shown in the Web UI
```

-------------------------------------------------------------------------------

## Installing Your App

To make your app accessible to Simmate and Python, you must "install" it in **editable mode**. This allows you to change your code and see the effects immediately without reinstalling.

In your terminal, navigate to your project folder and run:

``` bash
pip install -e .
```

You can verify the installation by trying to import your app in Python:

``` python
import warren_app
```

-------------------------------------------------------------------------------

## Registering Your App

Finally, you must tell Simmate to load your app. You can do this using the command line:

``` bash
simmate config add "warren_app.apps.WarrenAppConfig"
```

Verify that it was added successfully:

``` bash
simmate config show
```

You now have a fully functional Simmate App! In the next sections, we will add workflows and database tables to it.
