# Creating Simmate Apps

!!! tip
    If you prefer learning from full examples, you can explore other apps built with Simmate at [`src/simmate/apps`](https://github.com/jacksund/simmate/tree/main/src/simmate/apps)

-------------------------------------------------------------------------------

## Why create a Simmate App?

A custom Simmate app gives you the following features & advantages:

- [x] Utilizing a custom database table to store workflow results
- [x] Accessing workflows through the website interface
- [x] Accessing workflows from other scripts (e.g., using the `get_workflow` function)
- [x] Organizing the code from larger projects into smaller files
- [x] Sharing workflows within a team
- [x] Allowing others to install your workflows (e.g., after publishing a new paper)

To achieve this, we need to organize our Python code in a specific format (i.e., there are rules for file naming and content).

-------------------------------------------------------------------------------

## Creating New App Files

1. To start a new app, navigate to your desired folder for code storage and run:
``` bash
simmate create-app
```

2. You will see the creation of a new folder named `my_new_project`. Open it, you should find a series of new files:
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

3. Note the presence of a folder named `example_app`. This is where your code will reside. You can create as many app folders as needed, but this guide will focus on a single app.

-------------------------------------------------------------------------------

## Naming Your Project and App

!!! danger
    Once you've chosen a name, stick with it. Altering your project or app name post-installation can result in `ModuleNotFound` errors.

**Naming the Project**

1. Rename your folder from `my_new_project` to a name of your choice. Adhere to Python conventions by keeping your project name all lowercase and connected with underscores. For instance, `warren_lab` or `scotts_project` are suitable project names.

2. Open the file `new_project_project/pyproject.toml` and update the name here as well. For example:
``` toml
[project]
name = "scotts_project"  # <--- updated with your new name
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

3. Open the file `example_app/apps.py` and rename the class AND name property to match your app name. We also add labels for the web ui to use. For example:
``` python
from django.apps import AppConfig

class SimmateCleaseConfig(AppConfig):
    name = "simmate_clease"
    
    # These settings determine in the web ui (if you add a urls.py to your app)
    verbose_name = "CLEASE"  
    description_short = "utilities for running cluster-expanison calcs using CLEASE"
```

    !!! note
        While this file may seem trivial, it enables users to build complex apps that
        include many other apps / subapps. Beginners will likely never revisit this
        file.

-------------------------------------------------------------------------------

## Installing Your App

1. Open the `pyproject.toml` file. This file instructs Python on how to install your code (and it doesn't require much to install a package :smile:). As your project expands and requires other programs to be installed, you'll track them here. For now, no changes are needed.

2. While inside your new project folder, "install" the project to
your conda environment in "--editable" (-e) mode. This allows you to make changes to your code, and Python will automatically incorporate your changes.
``` bash
# replace "my_new_project" with the name of your project
cd my_new_project
pip install -e .
```

3. Verify the installation by running these lines in Python. You may need to restart your terminal/Spyder for this to work.
    ``` python
    # Update code to use your new names
    import example_app
    from example_app.apps import ExampleAppConfig
    ```

4. You now have an installed app! However, Simmate is still unaware
of its existence. We need to inform Simmate to load it.

-------------------------------------------------------------------------------

## Registering Your App

1. If you have explored the `Apps` section of our documentaion, you will see that many apps are registerd using the `simmate config add` command. We can use this command to register our app. Simply write out the python path to our `Config`:
``` bash
simmate config add 'example_app.apps.ExampleAppConfig'
```

    !!! note
        `ExampleAppConfig` is the python class that we defined in the `apps.py` file

2. Ensure the new configuration includes your new app:
``` bash
simmate config show --user-only
```

3. Ensure Simmate can locate and load your app in Python:
``` python
from simmate.configuration import settings

print(settings.apps)  # you should see your new app!
```

4. Ensure Simmate can configure your new app and its tables properly:
``` python
from simmate.database import connect
```

5. You now have registerd your app with Simmate and confirmed everything is working :rocket:

-------------------------------------------------------------------------------

## Sharing your app w. others

If you are an experienced python programmer, you probably noticed this already... But **Simmate Apps are essentially the creation of a new Python package.** In fact, our `start-project` command functions like [a "cookie-cutter" template](https://cookiecutter.readthedocs.io/en/stable/README.html).

This has significant implications for code and research sharing. With a fully-functional and published Simmate project, you can share your code with other labs via Github and PyPi. This allows the entire Simmate community to install and use your custom workflows with Simmate. For them, the process is as simple as:

1.  `pip install my_new_project`
2.  Adding `example_app.apps.ExampleAppConfig` to their `~/simmate/my_env-settings.yaml`

We won't cover publishing packages in our guides (because it's an advanced topic), but feel free to reach our to our team if you need help :smile:

!!! note
    Alternatively, you can request to merge your app into our Simmate repository, making it a default installation for all users. Whichever path you choose, your hard work will be more accessible to the community and new users!

-------------------------------------------------------------------------------
