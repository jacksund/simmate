## Overview

Workflows can incorporate any Python code, enabling them to invoke other workflows using the `run` or `run_cloud` methods. This functionality allows for the sequential execution of multiple workflows or their submission to a cluster for large-scale analyses.

## Running a Workflow Repeatedly

You can use the `run` method of a workflow within another workflow for repeated runs.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # no database table yet

    @staticmethod
    def run_config(structure, **kwargs):
    
        another_workflow = get_workflow("static-energy.vasp.mit")
        
        for n in range(10):
            structure.perturb(0.05)  # in-place modification
            state = another_workflow.run(structure=structure)
            result = state.result()
            # ... process the result
```

!!! note
    The `state.result()` call is used just like in a regular workflow run. The usage remains the same.

## Running Multiple Workflows

You can call a series of workflows on an input. The `run_config` accepts any Python code, so the workflow usage remains unchanged:

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

## Storing All Runs in a Shared Directory

To save the results of all workflows in a single location, manually set the directory for each subworkflow run:

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, directory, **kwargs):  
        another_workflow = get_workflow("static-energy.vasp.mit")
        for n in range(10):
            structure.perturb(0.05)
            
            subdirectory = directory / f"perturb_number_{n}"
            
            another_workflow.run(
                structure=structure,
                directory=subdirectory, # creates a subdirectory for this run
            )
```

!!! danger
    Do **NOT** share a working directory when using `run_cloud`. This can lead to problems when resources are distributed across different computers and file systems. Refer to github [#237](https://github.com/jacksund/simmate/issues/237) for more information.

## Transferring Results Between Runs

You can pass the result from one subworkflow to the next subworkflow by interacting with the database object.

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
        
        subworkflow_2 = get_workflow("static-energy.vasp.mit")
        state_2 = subworkflow_2.run(
            structure=result_1,  # use the final structure of the last calculation
        )
        result_2 = state_2.result()
        
        if result_2.energy_per_atom > 0:
            print("Structure is very unstable even after relaxing!")
            structure_new = result_2.to_toolkit()
            structure_new.scale_lattice(
                volume=structure.volume * 1.2,
            )
            state_2 = subworkflow_2.run(
                structure=structure_new,  # use the modified structure
            )
```

## Transferring Files Between Runs

A workflow can require a file from a previous calculation as an input. This can be specified using the `use_previous_directory` attribute, which copies files from the previous directory to the current one.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False
    use_previous_directory = ["filename1", "filename2"]

    @staticmethod
    def run_config(structure, directory, previous_directory, **kwargs):

        expected_file1 = directory / "filename1"
        assert expected_file1.exists()
        
        expected_file2 = directory / "filename2"
        assert expected_file2.exists()
```

Workflows with `use_previous_directory` set to True or a list of filenames MUST provide either a `previous_directory` parameter or a database object from a previous calculation as the `structure` parameter.

```python
workflow.run(previous_directory="path/to/my/folder")
```

```python
status = setup_workflow.run()
previous_result = status.result()

workflow.run(structure=previous_result)
```

!!! tip
    File copying/passing should be used for large files and data chunks. Small data pieces should be passed between workflows using Python objects and the database.

## Submitting Parallel Workflows

For situations where you don't want to wait for each workflow run to finish or need to submit hundreds of independent workflow runs, use the `run_cloud` command instead of `run`.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, **kwargs):
    
        another_workflow = get_workflow("static-energy.vasp.mit")
        
        submitted_states = []
        
        for n in range(10):
            structure.perturb(0.05)
            
            state = another_workflow.run_cloud(structure=structure)
            
            submitted_states.append(state)
            
        results = [state.result() for state in submitted_states]
        
        for result in results:
            print(result.energy_per_atom)
```

!!! danger
    Do **NOT** share a working directory when using `run_cloud`. This can lead to problems when resources are distributed across different computers and file systems. Refer to github [#237](https://github.com/jacksund/simmate/issues/237) for more information.

!!! tip
    The `state.result()` call to wait for each result is optional. You can even have a workflow that just submits runs and then shuts down without ever waiting on the results.