
# Welcome to your new Simmate project!

Make sure you have gone through our tutorials because making a custom project
can be difficult for those new to coding and Simmate!

Tutorials are at: https://github.com/jacksund/simmate/tree/main/tutorials



## Initial setup

To beign, let's do some intial setup and make sure Simmate is installed correctly:

1. With this new project as your working directory, we want to "install" the project to
your conda envirnment:

``` bash
# replace "my_new_project" with the name of your project
cd my_new_project
pip install -e .
```

2. Make sure this install worked by running these lines in python:

``` bash
# You may need to restart your terminal/Spyder for this to work
import example_app
from example_app.apps import ExampleAppConfig
```

3. Make sure this `example_app` is listed in your `~/simmate/applications.yaml`.
If this is your first project, the file contents should be...
``` yaml
example_app.apps.ExampleAppConfig
```

4. Reset your database, which will now build-in the new tables from `example_app`:

``` bash
simmate database reset
```

5. Make sure you can view the new tables in your database

``` python
from simmate.database import connect
from example_app.models import ExampleRelaxation

ExampleRelaxation.objects.count()  # should output 0 bc we haven't added data yet
```



## Rename the app

Now we can start editting our app and even adding new apps if we'd like.

1. rename your app folder from `example_app` to anything you'd like! Try
to keep it short and use underscores if you need multiple words.

2. Use this updated name to replace `example_app` listed in your
 `~/simmate/applications.yaml` and `example_app/apps.py` files. Also change the 
 Config class name `ExampleAppConfig` to match your app name. For example if 
 your new app name was `crazy_research`, you can change the class name 
 to `CrazyResearchConfig`

3. Reset your database again so that all tables are named after your app correctly: 

``` bash
simmate database reset
```



## Editting the app

Depending on what kind of project you'd like to build, the next steps can vary
greatly. To make sure you are going through the correct process, keep these
notes in mind:

- Start by reading each file and understanding it's role. Some you may never 
edit, and that's okay!

- Whenever you change the models.py file, be sure to either (1) reset your database
or (2) run `simmate database update` in order for your changes to be applied 
to your database.

- avoid renaming/moving your project or apps - as you will need to redo many of
 the steps above each time you do this.

- Advanced features can be tricky to figure out if you haven't coded before. 
Don't be afraid to post beginner question on our github.
