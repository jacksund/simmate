
# Build custom workflows

> :warning: There is no "quick tutorial" for this topic. Even advanced users should read everything!

In this tutorial, you will learn how to build customized workflows.

1. [Why isn't there a `custom_settings` option?](#why-isnt-there-a-custom_settings-option)
2. [Update settings for an existing workflow](#update-settings-for-an-existing-workflow)
3. [Determine a name for your new custom workflow](#determine-a-name-for-your-new-custom-workflow)
4. [Create new & advanced workflows](#create-new-&-advanced-workflows)
5. [Taking things to the next level](#taking-things-to-next-level)

</br></br>

## Why isn't there a `custom_settings` option?

We intentionally avoid the use of `workflow.run(custom_settings=...)`. **This will NOT work.** Simmate does this because we do not want to store results from customized settings in the same results table -- as this would (a) complicate analysis of many structures/systems and (b) make navigating results extremely difficult for beginners. For example, reducing the `ENCUT` or changing the dispersion correction of a VASP calculation makes it so energies cannot be compared between all materials in the table, and thus, features like calculated hull energies would become inaccruate.

Instead, Simmate encourages the creation of new workflows and result tables when you want to customize settings. This puts Simmate's emphasis on "scaling up" workflows (i.e. running a fixed workflow on thousands on materials) as opposed to "scaling out" workflows (i.e. a flexible workflow that changes on a structure-by-structure basis).

</br>

## Update settings for an existing workflow

For very quick testing, it is still useful to customize a workflow's settings without having to create a new workflow altogether. There are two approaches you can take to edit your settings:

**OPTION 1:** 

Writing input files and manually submitting a separate program

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

## Naming workflows

> :warning: Naming is very import! If you skip this step, your workflows will fail and cause errors elsewhere.

Naming your new workflow is an important step in Simmate. Features (such as the website interface) require that workflow names follow a certain format because this let's us do things such as determine where we can find your new workflow in the website interface. We follow a set of rules to arrive at workflow names like `relaxation.vasp.mit`.

First, we need to update the workflow name to match Simmate's naming
conventions, which includes:
1.  The type of analysis the workflow is doing
2.  The "calculator" (or program) that the workflow uses to run
3.  A unique name to identify the settings used

Examples for each part would be:
1. relaxation, static-energy, dynamics, ...
2. vasp, abinit, qe, deepmd, ...
3. jacks-test, matproj, quality00, ...

Together, an example workflow names would be:
- `relaxation.vasp.jacks-test`
- `static-energy.abinit.matproj`
- `dynamics.qe.quality00`

When converting this to our workflow name in python, we need to replace
periods with 2 underscores each and convert our words to
[pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/).
For example, our workflow names become:
- `Relaxation__Vasp__JacksTest`
- `StaticEnergy__Abinit__Matproj`
- `Dynamics__Qe__Quality00`

> :bulb: Capitalization is very important here so make sure you double check your workflow names.

Now let's test this out in python using a similar workflow name:
``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# These names can be long and unfriendly, so it can be nice to
# link them to a variable name for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Now check that our naming convention works as expected
assert my_workflow.name_full == "example.pure-python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_calculator == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

You now have a ready-to-use workflow name!

</br>

## Create new & advanced workflows

Simmate defines a base `Workflow` class to help with common material science analyses. The simplest possible workflow can look something like...

``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    # Note, the long name of this workflow class is important!
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42
```

Building a workflow from scratch can be a lot of work. Most often, we don't want to create a new workflow. We just want to take an existing one and update a few settings. In python, we can do that with...

``` python
from simmate.workflows.utilities import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):
    # NOTE: the name we gave is important! 
    # Don't skip reading the guide above
    
    # give a version to help you and you team keep track of what changes
    version = "2022.07.04"

    incar = original_workflow.incar.copy()  # Make sure you copy!
    incar.update(
        dict(
            NPAR=1,
            ENCUT=-1,
        )
    )

# make sure we have new settings updated and that we didn't change the original
assert original_workflow.incar != StaticEnergy__Vasp__MyCustomPreset
```

You can now run and interact with your workflow like any other one!

``` python
state = StaticEnergy__Vasp__MyCustomPreset.run(structure="NaCl.cif")
result = state.result()
```

There's much more that's possible. We'll look at a slightly more complex example in the next tutorial too. Be sure to keep going!

</br>

# Taking things to next level 

There are still a lot of things we would want to do with our new workflow. For example, what if we want to...
- modify a complex workflow (such as `diffusion.vasp.neb-all-paths-mit`)
- create a custom workflow using a new program like USPEX or ABINIT
- use a custom database table to save our workflow results
- access the workflow in the website interface
- access our workflow from other scripts (and the `get_workflow` function)

For creating complex workflows and databases, you'll need to read through our API documentation, where we cover advanced cases. Also, don't be hesitate to [post a question on our forum](https://github.com/jacksund/simmate/discussions/categories/q-a). We can also tell you the best place to start.

Accessing our workflow on the website or in scripts is much easier, and we will cover it in the next tutorial -- while we tackle custom database tables as the same time. Continue to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/07_Build_custom_datatables_and_apps.md) when you're ready.
