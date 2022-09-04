-------------------------------------------------------------------------------

# Creating new project files

1. To create a new project, navigate to a folder where you'd like to store your code and run...
``` bash
simmate start-project
```

2. Doublecheck that you see a new folder named `my_new_project`. Open it up and you should see a series of new files:
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

3. Make note that we have a folder named `example_app`. This is where our code will go. You can have as many app folders as you'd like (and in **extreme** scenarios even have apps within other apps).

-------------------------------------------------------------------------------

## Name our project and app

!!! danger
    One you choose a name, stick with it. Changing your project name or app name after it has
    been installed can lead your code failing with `ModuleNotFound` errors.
    
!!! tip
    This step is optional and where many mistakes happen. If you run into errors below, try restarting your project from scratch and leaving the default app names.

** Name the project **

1. Rename your folder from "my_new_project" to a name of your choosing. Try to follow python conventions and keep your project name all lowercase and connected with underscores. For example, `warren_lab` or `scotts_project` are good project names.

2. Open the file `new_project_project/pyproject.toml` and change the name here as well.
``` toml
[project]
name = "my_simmate_project"  # <--- update with your new name
```

!!! note
    We will explain these files in a later section. For now, just stick to renaming!

** Name the app **

1. Decide on how your code should be imported. For example, you may want your workflows to be loaded like so:
``` python
from my_app.workflows import Example__Workflow__Settings
```

2. Take the first part of this (`my_app`) and rename the `example_app` folder to match this. The python conventions (described above) also apply here. For example, `simmate_abinit` or `simmate_clease` are informative and good project names. These let the user know what's in your app and they're easy to remember. Here's how they would work:
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
    This file might seem silly, but it allows users to build complex apps that
    include many other apps / subapps. Beginners will likely never look at this
    file again.

-------------------------------------------------------------------------------

## Install our app

1. Open the `pyproject.toml` file. This file is what tells Python how to install your code. It doesn't take much to install a package :smile:. As you project gets larger and needs other programs installed, you'll make note of them here. For now, nothing needs to be changed.

2. While inside your new project folder, we want to "install" the project to
your conda envirnment in "--editable" (-e) mode. This means you'll be make changes to your code and Python should automatically use your changes.
``` bash
# replace "my_new_project" with the name of your project
cd my_new_project
pip install -e .
```

3. Make sure this install worked by running these lines in python. You may need to restart your terminal/Spyder for this to work.

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

You now have an installed app! But one issue remains: Simmate still doesn't know
it exists yet. We need to tell Simmate to load it.

-------------------------------------------------------------------------------

## Register your app with Simmate


1. Go to your simmate configuration folder. Recall from earlier tutorials that
this where your database is stored, and it is located at...
```
# in your home directory
~/simmate/
```

2. Look for the file `~/simmate/my_env-apps.yaml`, which is named after your
conda environment. If you don't see one, then make a new one!

3. In this file, add the following line:

=== "example 1"
    ``` yaml
    example_app.apps.ExampleAppConfig
    ```

=== "example 2"
    ``` yaml
    simmate_clease.apps.SimmateCleaseConfig
    ```

4. Make sure Simmate can find and load your app

=== "python"
    ``` python
    from simmate.configuration.django.settings import extra_apps
    print(extra_apps)  # you should see your new app!
    ```

5. Make sure Simmate can configure your new app and it's tables properly
=== "python"
    ``` python
    from simmate.database import connect
    ```


!!! tip
    If you ever want to stop using this app, you can delete it from your `~/simmate/my_env-apps.yaml` file.

-------------------------------------------------------------------------------
