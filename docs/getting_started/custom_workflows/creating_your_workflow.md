
# Create new & advanced workflows

!!! note 
    This guide only covers the bare-minimum. We highly recommend going through the full guides when building your custom workflows.

----------------------------------------------------------------------

## Create a flow from scratch

Simmate defines a base `Workflow` class to help with common material science analyses. The simplest possible workflow can look something like...

``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    # Note, the long name of this workflow class is important!
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42
```

----------------------------------------------------------------------

## Modify an existing workflow

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

!!! danger
    Updating workflows can often run into unexpected problems -- because not workflows
    behave the same. More often then not, you should create your own custom 
    `VaspWorkflow`. Learn more [in the full-guides](/full_guides/workflows/creating_new_workflows/#building-from-existing-workflows).
    

----------------------------------------------------------------------

## Running your workflow

You can now run and interact with your workflow like any other one!

``` python
state = StaticEnergy__Vasp__MyCustomPreset.run(structure="NaCl.cif")
result = state.result()
```

!!! tip
    You can also run workflows from a YAML file too. Check out the [full-guides](/full_guides/workflows/creating_new_workflows/#running-our-custom-workflow) to learn more.

----------------------------------------------------------------------
