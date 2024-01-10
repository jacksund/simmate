# Workflow Naming Guidelines

----------------------------------------------------------------------

## The Importance of Naming Conventions
In Simmate, the naming of your new workflow is a crucial step. 

Certain features, such as the website interface, necessitate that workflow names adhere to a specific format. This allows us to perform tasks such as locating your new workflow within the website interface. We follow a set of rules to generate workflow names like `relaxation.vasp.mit`.

Here's how a workflow name appears in different contexts:

=== "Readable Name"
    ```
    static-energy.vasp.matproj
    ```

=== "Website URL"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ```

=== "Python Class Name"
    ```
    StaticEnergy__Vasp__Matproj
    ```

----------------------------------------------------------------------

## Understanding Naming Conventions

Simmate's naming conventions consist of three components:

1.  The type of analysis the workflow performs
2.  The "app" (or program) that the workflow uses for execution
3.  A unique name to distinguish the settings used

Examples for each component are:

1. relaxation, static-energy, dynamics, ...
2. vasp, abinit, qe, deepmd, ...
3. jacks-test, matproj, quality00, ...

Combined, example workflow names would be:

- `relaxation.vasp.jacks-test`
- `static-energy.abinit.matproj`
- `dynamics.qe.quality00`

To convert this to our workflow name in python, we replace periods with two underscores each and convert our words to [pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). For instance, our workflow names become:

- `Relaxation__Vasp__JacksTest`
- `StaticEnergy__Abinit__Matproj`
- `Dynamics__Qe__Quality00`

!!! warning
    Be mindful of capitalization as it is crucial in this context. Always double-check your workflow names.

----------------------------------------------------------------------

## Implementing it in Python

Let's put this into practice in Python using a similar workflow name:
``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# These names can be lengthy and complex, so it's helpful to
# assign them to a variable name for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Now verify that our naming convention functions as expected
assert my_workflow.name_full == "example.python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_app == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

You now have a valid workflow name!

!!! tip
    `assert` essentially means "ensure this statement returns `True`". It's
    commonly used by Python developers to verify that their code functions as intended.

----------------------------------------------------------------------