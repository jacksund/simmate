# Constructing New & Advanced Workflows

!!! note 
    This guide provides a basic overview. For a comprehensive understanding when constructing your custom workflows, we strongly recommend referring to the complete guides.

----------------------------------------------------------------------

## Building a Workflow from Scratch

Simmate offers a foundational `Workflow` class to assist with routine material science analyses. The most basic workflow could appear as follows...

``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    # Remember, the extended name of this workflow class is crucial!
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42
```

----------------------------------------------------------------------

## Altering an Existing Workflow

Creating a workflow from scratch can be time-consuming. More often than not, we simply want to modify an existing workflow by updating a few settings. This can be achieved in Python as follows...

``` python
from simmate.workflows.utilities import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):
    # NOTE: The name we assigned is crucial! 
    # Don't overlook the guide above
    
    # Assign a version to help you and your team track changes
    version = "2022.07.04"

    incar = original_workflow.incar.copy()  # Always make a copy!
    incar.update(
        dict(
            NPAR=1,
            ENCUT=-1,
        )
    )

# Ensure the new settings are updated and that the original remains unchanged
assert original_workflow.incar != StaticEnergy__Vasp__MyCustomPreset
```

!!! danger
    Modifying workflows can often lead to unforeseen issues -- as not all workflows
    behave identically. More often than not, it's advisable to create your own custom 
    `VaspWorkflow`. Learn more [in the full-guides](/simmate/full_guides/workflows/creating_new_workflows/#building-from-existing-workflows).
    

----------------------------------------------------------------------

## Executing your Workflow

You can now execute and interact with your workflow like any other!

``` python
state = StaticEnergy__Vasp__MyCustomPreset.run(structure="NaCl.cif")
result = state.result()
```

!!! tip
    Workflows can also be executed from a YAML file. Refer to the [full-guides](/simmate/full_guides/workflows/creating_new_workflows/#running-our-custom-workflow) for more information.

----------------------------------------------------------------------

# Advanced Workflow Features

There are numerous enhancements you may want to incorporate into your new workflow. For instance, you might want to:

- [x] Modify a complex workflow (like `diffusion.vasp.neb-all-paths-mit`)
- [x] Develop a custom workflow using a new program such as USPEX or ABINIT
- [x] Utilize a custom database table to store your workflow results
- [x] Access the workflow via the website interface
- [x] Access your workflow from other scripts (and the `get_workflow` function)

These topics will be addressed in the next tutorial, where we will simultaneously cover custom database tables.

----------------------------------------------------------------------
