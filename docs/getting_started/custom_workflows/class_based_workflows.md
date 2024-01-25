# Class-based Workflows

----------------------------------------------------------------------

## Switching to classes

We now know that all workflows are really just python functions (+ some automatic functionality added on top). However, advanced python users will run into trouble here... This is because functions are not as powerful as classes when it comes to organizing and reusing code.

Simmate therefore let's you build workflows from a `Workflow` class, rather than the `@workflow` function decorator. In order to convert our function to a `Workflow` class, we must do the following:

- set the class name using Simmate conventions *(we cover this in the next section)*
- define a `run_config` method
- add `@staticmethod` or `@classmethod` to `run_config`


Taking our `add` workflow from the previous tutorial:

``` python
from simmate.engine import Workflow

class Math__Basic__Add(Workflow):

    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(x, y, **kwargs):
        return x + y

# running is the same as before
status = Math__Basic__Add.run(x=1, y=2)
result = status.result()
```

Nothing has changed with our workflow -- it just looks a little more complex. Writing workflows in this way might seem silly at first, but class-based workflows make advanced features MUCH easier to implement. 

We will demonstrate this in the `App-based Workflows` section. For now, let's focus on our crazy class name (`Math__Basic__Add`) and why we chose that.

!!! note
    This new `Workflow` format is all you need to understand about class-based workflows for now. Other details are not relevent to beginners, so please refer to the full guides for more information

----------------------------------------------------------------------

## Workflow Naming Guidelines

### Importance of Naming

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

!!! example
    `Math__Basic__Add` becomes `math.basic.add`, and once placed in a custom app, this workflow can be found in the website at `http://localhost:8000/workflows/math/basic/add`

### Understanding Naming Conventions

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