
# Building custom workflows

> :warning: This tutorial isn't required for beginners to use Simmate. There is currently no "quick tutorial" for this topic as this is only for advanced users with complex use-cases.

In this tutorial, you will learn how to build customized workflows. This involves an introduction to underlying calculators and workflow engine features.

1. [Why isn't there a `custom_settings` option?](#why-isnt-there-a-custom_settings-option)
2. [Update settings for an existing workflow](#update-settings-for-an-existing-workflow)
2. [Create new & advanced workflows](#create-new-&-advanced-workflows)
3. [Creating a Project for our workflow](#creating-a-project-for-our-workflow)

</br>

## Why isn't there a `custom_settings` option?

We intentionally avoid the use of `workflow.run(custom_settings=...)`. **This will NOT work.** Simmate does this because we do not want to store results from customized settings in the same results table -- as this would (a) complicate analysis of many structuers/systems and (b) make navigating results extremely difficult for beginners. For example, reducing the `ENCUT` or changing the dispersion correction of a VASP calculation makes it so energies cannot be compared between all materials in the table, and thus, features like calculated hull energies would become inaccruate.

Instead, Simmate encourages the creation of new workflows and result tables when you want to customize settings. This puts Simmate's emphasis on "scaling up" workflows (i.e. running a fixed workflow on thousands on materials) as opposed to "scaling out" workflows (i.e. a flexible workflow that changes on a structure-by-structure basis).

</br>

## Update settings for an existing workflow

For very quick testing, it is still useful to customize a workflow's settings without having to create a new workflow altogether. There are two approaches you can take to edit your settings:

**OPTION 1:** Writing input files and manually submitting a separate program

``` bash
# This simply writes input files
simmate workflows setup-only static-energy.vasp.mit --structure POSCAR

# access your files in the new directory
cd static-energy.vasp.mit.SETUP-ONLY

# Customize input files as you see fit.
# For example, you may want to edit INCAR settings
nano INCAR

# You can then submit VASP manually. Note, this will not use
# simmate at all! So there is no error handling and no results
# will be saved to your database.
vasp_std > vasp.out
```

**OPTION 2:** Using the "customized" workflow for a calculator (e.g. `customized.vasp.user-config`)

``` yaml
# In a file named "my_example.yaml".

# Indicates we want to change the settings, using a specific workflow as a starting-point
workflow_name: customized.vasp.user-config
workflow_base: static-energy.vasp.mit

# The parameters starting with "custom__" indicates we are updating some class 
# attribute. These fundamentally change the settings of a workflow.
# Currently, only updating dictionary-based attributes are supported
custom__incar: 
    ENCUT: 600
    KPOINTS: 0.25
custom__potcar_mappings:
    Y: Y_sv

# Then the remaining inputs are the same as the base workflow
structure: POSCAR
command: mpirun -n 5 vasp_std > vasp.out
```

``` bash
# Now run our workflow from the settings file above.
# Results will be stored in a separate table from the
# base workflow's results.
simmate workflows run-yaml my_example.yaml
```

Both of these approaches are only suitable for customizing settings for a few calculations -- and also you lose some key Simmate features. If you are submitting many calculations (>20) and this process doesn't suit your needs, keep reading!

</br>

## Create new & advanced workflows

1. Simmate defines a base `Workflow` class to help with common material science analyses, but at its core, it uses Prefect Flows. Therefore, if you don't care for advanced Simmate features, you can build custom workflows directly with Prefect. Take advantage of all of [Prefect's guides](https://orion-docs.prefect.io/tutorials/first-steps/) when building new workflows. The simplest possible workflow can look something like...

``` python
from prefect import flow

@flow
def my_favorite_function():
    print("This function doesn't do much")
    return 42

state = my_favorite_function()
result = state.result()
```

2. However, we've built many helpful features on top of Simmate to make your workflows more powerful and easier to write. In building a material science workflow, we may want two common steps: (i) running a calculation through a program like VASP and (ii) saving the results to our database. We must therefore define individual `Task`s as well as a `DatabaseTable` to store results in. The next steps will address both of these.

3. Because material science frequently involves calling external programs, we've created a powerful `S3Task` class to inherit from. A `S3Task` class can implement it's own `setup`, `execute`, and `workup` methods, and even add functions for error handling. Here's how you would build a custom `S3Task` from scratch:

``` python

from simmate.toolkit import Structure
from simmate.workflow_engine import S3Task


class ExampleTask(S3Task):

    command = "echo 'I am calling some program here!' > output.txt"
    
    @staticmethod
    def setup(directory, structure, **kwargs):
        filename = directory / "my_input_structure.cif"
        structure.to("cif", filename)

    @staticmethod
    def workup(directory):
        # do some workup or analysis on the output files. Here we just return
        # the original structure back as the "results"
        filename = directory / "my_input_structure.cif"
        my_results = Structure.from_file(filename)
        return my_results


# Now try running this task using a test NaCl structure
nacl_example = Structure(
    lattice=[
        [3.485437, 0.0, 2.012318],
        [1.161812, 3.286101, 2.012318],
        [0.0, 0.0, 4.024635],
    ],
    species=["Na", "Cl"],
    coords=[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]],
)

# Tasks classes don't need to be initialized. You can call them directly.
state = ExampleTask.run(structure=nacl_example)
result = state.result()

# The output is a dictionary containing the return value from the workup 
# method along with other information about the task run.
print(result)  
```


4. Building a task `S3Task` from scratch can be a lot of work. Instead, you may want to inherit from tasks we built already. To see what programs are available, take a look at the `simmate.calculators` module ([here](https://github.com/jacksund/simmate/tree/main/src/simmate/calculators)). For example, VASP users can use the `VaspTask`:

```python
from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS

class ExampleRelaxation(VaspTask):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS
    incar = dict(
        PREC="Low",
        EDIFF__per_atom=2e-4,  # flags like "__per_atom" help set structure-dependant settings
        EDIFFG=-2e-1,
        NSW=75,
        IBRION=2,
        POTIM=0.02,
        KSPACING=0.75,
    )

state = ExampleRelaxation.run(structure=...)
```

> :bulb: If you don't care to store results in a database, then the S3Task is all you need! Thus, all steps below can be considered optional (but they are highly recommended!).

5. Now let's create a database table to save our results. For this, we can either create a table from scratch or make one using the classes from `simmate.database.base_data_types`. Below is an example of how to build a table from structure and energy information.
``` python
from simmate.database import connect
from simmate.database.base_data_types import (
    table_column,
    Structure,
    Thermodynamics,
    Calculation,
)

class MyCustomTable(Structure, Thermodynamics, Calculation):
    class Meta:
        app_label = "workflow_results"

    custom_column_01 = table_column.IntegerField()
    custom_column_02 = table_column.FloatField(null=True, blank=True)

# Check out all the columns that are automatically built for us!
MyCustomTable.show_columns()

# IMPORTANT: This line will raise an error because, even though we 
# defined our table, we have not yet added it to our actual database.
# We will fix this in a later step.
MyCustomTable.objects.count()
```

6. Thus far, the process of creating a `S3Task` and a `DatabaseTable` are very common steps. It is also very common to piece these together into a single-calculation workflow (like we mentioned in step 2). Therefore, the default settings on the `Workflow` class does this for us automatically:

``` python
from simmate.workflow_engine import Workflow

# IMPORTANT: Note the complex name we used here! All workflows should follow
# our standardized naming conventions in order for the workflow to work 
# properly with cloud and website features.

class Relaxation__Vasp__MyCustomSettings(Workflow):
    s3task = ExampleRelaxationTable
    database_table = MyCustomTable


# Running the workflow acts exactly like how we ran the task, except now 
# we include saving results to a database table.
# IMPORTANT: This workflow will fail because we still have not registered
# our database table above! We'll get the same exact error as seen in the
# last step.
result = workflow.run(structure=structure) 
```

7. Thus far, we have built all of the code we need for a custom workflow, but we still have that pesky problem of our database table throwing a `does not exist` error. In the next section, we are going to take all of this code and organize it into an "app". This is important because it let's Simmate know where to find your defined database tables, tasks, and workflows.


</br>

## Creating a Project for our workflow

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


For expert python users, you may notice that you are building the start of a new python package here. In fact our "start-project" command is really just a cookie-cutter template! This can have huge implications for sharing research and code. With a fully-functional and published Simmate app, you can upload your project for other labs to use via github and PyPi! Then the entire Simmate community can install and use your custom workflows with Simmate. For them, it'd be as easy as doing (i) `pip install my_new_project` and (ii) adding `example_app.apps.ExampleAppConfig` to their `~/simmate/applications.yaml`. Alternatively, you can request that your app be merged into our Simmate repository, so that it is installed by default for all users. Whichever route you choose, your hard work should be much more accessible to the community and new users!

> :warning: In the future, we hope to have a page that lists off apps available for download, but because Simmate is brand new, there currently aren't any existing apps outside of Simmate itself. Reach out to our team if you're interesting in kickstarting a downloads page!

Up next, we will start sharing results with others! Continue to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/07_Use_a_cloud_database.md) when you're ready.
