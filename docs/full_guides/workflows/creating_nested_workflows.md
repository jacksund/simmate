## Overview

Workflows can incorporate any Python code, enabling them to invoke other workflows using the `run` or `run_cloud` methods. This is useful for sequential execution or submitting many sub-tasks to a cluster.

## Using `StagedWorkflow` (Recommended)

For sequential calculations where each step uses the result of the previous one (e.g., a series of relaxations with increasing quality), Simmate provides the `StagedWorkflow` class. This is the preferred way to chain workflows.

``` python
from simmate.workflows.base_flow_types import StagedWorkflow

class Relaxation__Vasp__StagedExample(StagedWorkflow):
    """
    Runs three relaxations of increasing quality.
    """
    
    subworkflow_names = [
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
    ]
```

When you call `Relaxation__Vasp__StagedExample.run(structure=my_structure)`, Simmate will:

1. Run `quality00` using `my_structure`.
2. Take the final structure from `quality00` and use it as input for `quality01`.
3. Take the final structure from `quality01` and use it as input for `quality02`.

`StagedWorkflow` also handles:

- Creating subdirectories for each step (e.g., `quality00`, `quality01`, etc.).
- Copying necessary files between steps (using `files_to_copy`).
- Aggregating results from all steps into a single database entry.

!!! tip
    `StagedWorkflow` is ideal for building robust pipelines that handle randomly-generated structures where an initial low-quality relaxation can save significant time.

## Manual Chaining

You can also manually chain workflows within a `run_config` method. This is useful when you need custom logic between steps.

### Transferring Results

``` python
from simmate.workflows.utilities import get_workflow
from simmate.workflows import Workflow

class Example__Python__CustomChain(Workflow):
    
    use_database = False

    @staticmethod
    def run_config(structure, directory, **kwargs):
    
        subworkflow_1 = get_workflow("relaxation.vasp.mit")
        result_1 = subworkflow_1.run(structure=structure)
        
        subworkflow_2 = get_workflow("static-energy.vasp.mit")
        result_2 = subworkflow_2.run(
            structure=result_1,  # use the result of the first calculation
        )
```

### Transferring Files

A workflow can require files from a previous calculation using the `use_previous_directory` attribute.

``` python
class Example__Python__FileTransfer(Workflow):
    
    use_database = False
    use_previous_directory = ["CHGCAR", "WAVECAR"]

    @staticmethod
    def run_config(structure, directory, previous_directory, **kwargs):
        # Files are already copied into `directory` at this point
        pass
```

!!! danger
    Do **NOT** share a working directory when using `run_cloud`. This can lead to race conditions or file corruption on distributed systems.

## Submitting Parallel Workflows

For situations where you don't want to wait for each workflow run to finish or need to submit hundreds of independent workflow runs, use the `run_cloud` command instead of `run`.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.workflows import Workflow

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