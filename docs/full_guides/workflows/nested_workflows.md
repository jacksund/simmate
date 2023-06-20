
----------------------------------------------------------------------

## Overview

Because workflows can contain any python code, they can also make calls to
other workflows -- either via `run` or `run_cloud` methods.

This enables calling one or serveral workflows in succession -- or even submitting
them to the cluster if you have many analyses to run.

----------------------------------------------------------------------

## Calling one workflow repeatedly

You can use the `run` method of a workflow within another workflow and call it as much as you'd like.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(structure, **kwargs):
    
        # you can grab a workflow locally, attach one as a class
        # attribute, or anything else possible with python
        another_workflow = get_workflow("static-energy.vasp.mit")
        
        # And run the workflow how you would like. Here, we are
        # just running the workflow 10 times in row on different
        # perturbations or "rattling" of the original structure
        for n in range(10):
            structure.perturb(0.05)  # modifies in-place
            state = another_workflow.run(structure=structure)
            result = state.result()
            # ... do something with the result
```

!!! note
    Notice that we are calling `state.result()` just like we would a normal workflow run. Usage is exactly the same.

----------------------------------------------------------------------

## Calling multiple workflows

You can also call a series of workflows on an input. Again, any python will
be accepted within the `run_config` so workflow usage does not change:

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, directory, **kwargs):
    
        subworkflow_1 = get_workflow("static-energy.vasp.mit")
        subworkflow_1.run(structure=structure)
        
        subworkflow_2 = get_workflow("population-analysis.vasp.elf-matproj")
        subworkflow_2.run(structure=structure)
        
        subworkflow_3 = get_workflow("electronic-structure.vasp.matproj-full")
        subworkflow_3.run(structure=structure)      
```

----------------------------------------------------------------------

## Writing all runs to a shared directory

When using run, you often want workflows to share a working directory, so that you can find the results all in one place.

To do this, we simply need to set the directory manually for each subworkflow run:

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, directory, **kwargs):  # <-- uses directory as an input
        another_workflow = get_workflow("static-energy.vasp.mit")
        for n in range(10):
            structure.perturb(0.05)
            
            # make sure the directory name is unique
            subdirectory = directory / f"perturb_number_{n}"
            
            another_workflow.run(
                structure=structure,
                directory=subdirectory, # <-- creates a subdirectory for this run
            )
```

!!! tip
    Also see [writing output files](/simmate/full_guides/workflows/creating_new_workflows/#writing-output-files)

!!! danger
    when using `run_cloud` you should **NOT** share a working directory. This
    causes problems when you have computational resource scattered accross 
    different computers & file systems.
    See github [#237](https://github.com/jacksund/simmate/issues/237).

----------------------------------------------------------------------

## Passing results between runs

When you grab the result from one subworkflow, you can interact with that database
object to pass the results to the next subworkflow. 

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, directory, **kwargs):
    
        subworkflow_1 = get_workflow("relaxation.vasp.mit")
        state_1 = subworkflow_1.run(structure=structure)
        result_1 = state_1.result()
        
        # When passing structures, we can directly use the result. This is
        # because the 'structure' parameter accepts database objects as input.
        subworkflow_2 = get_workflow("static-energy.vasp.mit")
        state_2 = subworkflow_2.run(
            structure=result_1,  # use the final structure of the last calc
        )
        result_2 = state_2.result()
        
        # Alternatively, you may want to mutate or analyze the result in 
        # some way before submitting a new calculations
        if result_2.energy_per_atom > 0:
            print("Structure is very unstable even after relaxing!")
            # maybe the atoms are too close, so let's increase the volume by 20%
            structure_new = result_2.to_toolkit()
            structure_new.scale_lattice(
                volume=structure.volume * 1.2,
            )
            # and try the workflow again
            state_2 = subworkflow_2.run(
                structure=structure_new,  # use the modified structure
            )
```

----------------------------------------------------------------------

## Passing files between runs

Sometimes a workflow requires a file from a previous calculation as
an input. You can specify these flows with the `use_previous_directory` attribute,
which effectly means "use this previous directory to copy over files into our current
one".


**Setting the parameter:**
When set to `True`, the entire previous directory will be copied to the new
folder. Alternatively, this can be set to a list of filenames that will
be selectively copied over from the previous directory to the new one.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False
    use_previous_directory = ["filename1", "filename2"]

    @staticmethod
    def run_config(structure, directory, previous_directory, **kwargs):

        # before this run_config starts, simmate will have copied over
        # the files from our `previous_directory` parameter.
        # To show that, we can just confirm those files exist here.
        
        expected_file1 = directory / "filename1"
        assert expected_file1.exists()
        
        expected_file2 = directory / "filename2"
        assert expected_file2.exists()

# Examples of how to run this workflow are below
```

**How previous directory is detected:**

Workflows that have this set to True or a list of filenames MUST provide
one of the two: 

1. `previous_directory` parameter
2. a database object from a previous calculation as the `structure` parameter

Option 1 is the most straightforward and intuitive. We can set the previous directory where
our files can be found using the `previous_directory` parameter:

```python
workflow.run(previous_directory="path/to/my/folder")
```

Option 2 is a shortcut for Simmate database objects (see [the section prior to this one](##passing-results-between-runs)). If the result of another workflow is passed as the `structure`
parameter, we can infer the previous directory from that past run:

```python
# using some other workflow as a starting point
status = setup_workflow.run()
previous_result = status.result()

# Then this next workflow has `use_previous_directory` set.
# `previous_directory` is automatically set to `previous_result.directory`
workflow.run(structure=previous_result)
```


!!! tip
    As a general rule of thumb, file copying/passing should only be used for
    large files and chunks of data such as voxel data. Meanwhile, small pieces 
    of data should be passed between workflows using python objects and the 
    database (see section above this one).

----------------------------------------------------------------------

## Submitting parallel workflows

Sometimes, we don't want to pause and wait for each workflow run to finish. There are even cases where we would submit hundreds of workflow runs that are indpendent and can run in parallel.

To do this, we can use the `run_cloud` command instead of calling `run`.
``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(structure, **kwargs):
    
        another_workflow = get_workflow("static-energy.vasp.mit")
        
        # keep track of the runs we submit
        submitted_states = []
        
        for n in range(10):
            structure.perturb(0.05)  # modifies in-place
            
            # submit to cloud instead of running locally
            state = another_workflow.run_cloud(structure=structure)
            
            # add the state to our list
            submitted_states.append(state)
            
            # do NOT call result yet! This will block and wait for this 
            # calculation to finish before continuing
            # state.result()
        
        # now wait for all the calculations to finish and grab the results
        results = [state.result() for state in submitted_states]
        
        # And workup the results as you see fit
        for result in results:
            print(result.energy_per_atom)

```

!!! danger
    when using `run_cloud` you should **NOT** share a working directory. This
    causes problems when you have computational resource scattered accross 
    different computers & file systems.
    See github [#237](https://github.com/jacksund/simmate/issues/237).

!!! tip
    Using `state.result()` to wait for each result is optional too -- you decide when to call it (if at all). You can even have a workflow that just submits runs and then shuts down -- without ever waiting on the results.


----------------------------------------------------------------------
