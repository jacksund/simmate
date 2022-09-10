
# Naming workflows

----------------------------------------------------------------------

## Why are there naming rules?
Naming your new workflow is an important step in Simmate. 

Features (such as the website interface) require that workflow names follow a certain format because this let's us do things such as determine where we can find your new workflow in the website interface. We follow a set of rules to arrive at workflow names like `relaxation.vasp.mit`.

For example, here's how a workflow name looks in different contexts:

=== "readable name"
    ```
    static-energy.vasp.matproj
    ```

=== "website url"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ```

=== "python class name"
    ```
    StaticEnergy__Vasp__Matproj
    ```

----------------------------------------------------------------------

## Overview of naming conventions

Simmate's naming conventions involves 3 parts:

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

!!! warning
    Capitalization is very important here so make sure you double check your workflow names.

----------------------------------------------------------------------

## Trying it out in python

Now let's test this out in python using a similar workflow name:
``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# These names can be long and unfriendly, so it can be nice to
# link them to a variable name for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Now check that our naming convention works as expected
assert my_workflow.name_full == "example.python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_calculator == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

You now have a ready-to-use workflow name!

!!! tip
    `assert` effectively means "make sure this statement returns `True`". It's
    frequently used by python coders to make sure their code works as expected.

----------------------------------------------------------------------
