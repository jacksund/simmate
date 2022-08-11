
# Build custom database tables and apps

> :warning: There is no "quick tutorial" for this topic. Even advanced users should read everything!

In this tutorial, you will learn how to build customized database table and also learn how to build out your customized features into "projects" (or "apps").

1. [Should I create a Simmate project](#simmate-projects-and-why-to-make-them)
2. [Creating a new project](#creating-a-new-project)
3. [Creating a custom database table](#creating-a-custom-database-table)

</br></br>

## Should I create a Simmate project?

Whether you're a beginner or expert, building a big project or small one: the answer is 100% yes. :fire::fire::rocket:

At the end of the last tutorial, we posed a number of ideas. What if we wanted to...
- use a custom database table to save our workflow results
- access the workflow in the website interface
- access our workflow from other scripts (and the `get_workflow` function)

On top of these, we might also want to...
- share workflows among a team
- let others install your workflows after you publish a new paper

All of these can be done using Simmate "projects". These projects are really just a folder of python files in a specific format (i.e. we have rules for naming files and what to put in them).

For expert python users, you will notice that projects are building a new python package. In fact our "start-project" command is really just a cookie-cutter template! This can have huge implications for sharing research and code. With a fully-functional and published Simmate project (or "app"), you can upload your project for other labs to use via Github and PyPi! Then the entire Simmate community can install and use your custom workflows with Simmate. For them, it'd be as easy as doing (i) `pip install my_new_project` and (ii) adding `example_app.apps.ExampleAppConfig` to their `~/simmate/applications.yaml`. Alternatively, you can request that your app be merged into our Simmate repository, so that it is installed by default for all users. Whichever route you choose, your hard work should be much more accessible to the community and new users!

> :bulb: In the future, we hope to have a page that lists off apps available for download, but because Simmate is brand new, there currently aren't any existing apps outside of Simmate itself. Reach out to our team if you're interested in kickstarting a downloads page!

</br>

## Creating a new project

1. Let's create a project named `my_new_project`. To do this, navigate to a folder where you'd like to store your code and run...

``` bash
simmate start-project my_new_project
```

2. You will see a new folder named "my_new_project" which you can switch into.

``` bash
cd my_new_project
```

3. Open up the `README.md` file in this folder and read through our directions. If you want a web-form of this guide, use [this link](https://github.com/jacksund/simmate/tree/main/src/simmate/configuration/example_project)

4. After completing the steps in that readme, you've now registered your workflow and database tables to simmate!

</br>

## Creating custom database tables

Inside your project, there are example database tables that show how to build simple ones. It may seems super minimal, but there's really nothing else to do! 

Recall from [the section on inheritance](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md#the-full-tutorial) from tutorial 04. This is why building out new tables is so easy!

Some thing as simple as...

``` python
from simmate.database.base_data_types import (
    table_column,
    Structure,
)


class MyCustomTable1(Structure):
    new_column = table_column.FloatField(null=True, blank=True)
```

... will build out a new database table with all the following columns

```
- created_at
- updated_at
- source
- structure_string
- nsites
- nelements
- elements
- chemical_system
- density
- density_atomic
- volume
- volume_molar
- formula_full
- formula_reduced
- formula_anonymous
- spacegroup (relation to Spacegroup)
- new_column  # <--- note your new column here!
```

You can automatically fill this table using the `from_toolkit` method too:

``` python
from simmate.toolkit import Structure


nacl = Structure.from_file("NaCl.cif")

new_entry = MyCustomTable1.from_toolkit(
    structure=nacl, 
    new_column=3.1415,
)
new_entry.save()
```

There are many more `base_data_types` that you can use, and all types build out features for you automatically. Be sure to read through our guides in the [`simmate.database`](https://jacksund.github.io/simmate/simmate/database.html) module for more info. Advanced database tables may require reading more on the [base data types](https://jacksund.github.io/simmate/simmate/database/base_data_types.html) too.

</br>

## Time to starting sharing and scaling out!

Up next, we will start sharing results with others! Continue to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/08_Use_a_cloud_database.md) when you're ready.
