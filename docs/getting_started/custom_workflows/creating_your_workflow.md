
# Create new & advanced workflows

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
