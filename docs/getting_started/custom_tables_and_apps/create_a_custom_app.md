# Creating New Project Files

1. To initiate a new project, navigate to your desired folder for code storage and execute...
``` bash
simmate start-project
```

2. Verify the creation of a new folder named `my_new_project`. Upon opening, you should find a series of new files:
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

3. Note the presence of a folder named `example_app`. This is where your code will reside. You can create as many app folders as needed, and in **extreme** cases, even nest apps within other apps.

-------------------------------------------------------------------------------

## Naming Your Project and App

!!! danger
    Once you've chosen a name, stick with it. Altering your project or app name post-installation can result in `ModuleNotFound` errors.

**Naming the Project**

1. Rename your folder from "my_new_project" to a name of your choice. Adhere to Python conventions by keeping your project name all lowercase and connected with underscores. For instance, `warren_lab` or `scotts_project` are suitable project names.

2. Open the file `new_project_project/pyproject.toml` and update the name here as well.
``` toml
[project]
name = "my_simmate_project"  # <--- update with your new name
```

**Naming the App**

1. Determine how your code should be imported. For instance, you may want your workflows to be loaded like so:
``` python
from example_app.workflows import Example__Workflow__Settings
```

2. Use the first part of this (`example_app`) to rename the `example_app` folder. The Python conventions (described above) also apply here. For instance, `simmate_abinit` or `simmate_clease` are informative and memorable project names. Here's how they would work:
``` python
from simmate_clease.workflows import ClusterExpansion__Clease__BasicSettings
```

3. Open the file `example_app/apps.py` and rename the class AND name property to match your app name.
``` python
from django.apps import AppConfig

class SimmateCleaseConfig(AppConfig):  # don't forget the class name
    name = "simmate_clease"
```

!!! note
    While this file may seem trivial, it enables users to build complex apps that
    include many other apps / subapps. Beginners will likely never revisit this
    file.

-------------------------------------------------------------------------------

## Installing Your App

1. Open the `pyproject.toml` file. This file instructs Python on how to install your code. It doesn't require much to install a package :smile:. As your project expands and requires other programs to be installed, you'll note them here. For now, no changes are needed.

2. While inside your new project folder, "install" the project to
your conda environment in "--editable" (-e) mode. This allows you to make changes to your code, and Python will automatically incorporate your changes.
``` bash
# replace "my_new_project" with the name of your project
cd my_new_project
pip install -e .
```

3. Verify the installation by running these lines in Python. You may need to restart your terminal/Spyder for this to work.

=== "example 1"
    ``` python
    import example_app
    from example_app.apps import ExampleAppConfig
    ```

=== "example 2"
    ``` python
    import simmate_clease
    from simmate_clease.apps import SimmateCleaseConfig
    ```

You now have an installed app! However, Simmate is still unaware
of its existence. We need to inform Simmate to load it.

-------------------------------------------------------------------------------

## Registering Your App with Simmate

1. Navigate to your Simmate configuration folder. Recall from earlier tutorials that
this is where your database is stored, and it is located at...
```
# in your home directory
cd ~/simmate/
```

2. Locate the file `~/simmate/my_env-settings.yaml`, which is named after your
conda environment. Open it and you'll see we have apps already installed
with Simmate:
``` yaml
apps:
    - simmate.workflows.configs.BaseWorkflowsConfig
    - simmate.apps.VaspConfig
    - simmate.apps.BaderConfig
    - simmate.apps.EvoSearchConfig
```

3. In this section, add the following line:
``` yaml
- example_app.apps.ExampleAppConfig
```

4. Ensure Simmate can locate and load your app in Python
``` python
from simmate.configuration import settings
print(settings.apps)  # you should see your new app!
```

5. Ensure Simmate can configure your new app and its tables properly
``` python
from simmate.database import connect
```

-------------------------------------------------------------------------------