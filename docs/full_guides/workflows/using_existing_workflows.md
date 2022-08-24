
# Using existing workflows


## Loading a workflow

To import a specific workflow, see the `simmate.workflows` module. For all the
examples below, we will look at the `static-energy.vasp.matproj` workflow,
which we load with:
    
``` python
from simmate.workflows.all import StaticEnergy__Vasp__Matproj as workflow
```

Alternatively, you can also use `get_workflow` to load your workflow:
    
``` python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.matproj")
```


## Viewing input parameters

A workflow's input parameters can be analyzed in the following ways:

``` python
workflow.show_parameters()  # prints out info
workflow.parameter_names
workflow.parameter_names_required
```


## Running a workflow (local)

To run a workflow locally (i.e. directly on your current computer), you can
use the `run` method. As a quick example:

``` python
state = workflow.run(
    structure="NaCl.cif", 
    command="mpirun -n 4 vasp_std > vasp.out",
)

if state.is_completed():  # optional check
    result = state.result()
```

Note that `run` returned a `State` object, not our result. States allows you to
check if the run completed successfully or not. Then final output of your
workflow run can be accessed using `state.result()`. The `State` is based off
of Prefect's state object, which you can read more about 
[here](https://orion-docs.prefect.io/concepts/states/). We use `State`s because 
the status of a run becomes important when we start scheduling runs to run
remotely, and more importantly, it allows use to building in compatibility with
other workflow engines like Prefect.

Outside of python, you can also run workflows from the command line, using YAML 
files, or the website interface. These approaches are covered in the intro
tutorials.


## Running a workflow (cloud)

When you want to schedule a workflow to run elsewhere, you must first make sure
you have your computational resources configured. You can then run workflows
using the `run_cloud` method, which returns a Prefect flow run id.

``` python
run_id = workflow.run_cloud(
    structure="NaCl.cif", 
    command="mpirun -n 4 vasp_std > vasp.out",
)
```

On the computer where you want to actually run the workflow, start a worker
that will pick up and run the workflow you just scheduled:

``` bash
# NOTE: This worker will run endlessly.
# To control shutdown, see the Worker documentation.
simmate workflow-engine start-worker
```

If you want better control of which workers select a given workflow, you can
use `tags` to label your submission and worker.

``` python
run_id = workflow.run_cloud(
    structure="NaCl.cif", 
    tags=["my-custom-tag1", "quick-job"]
)
```

``` bash
simmate workflow-engine start-worker -t my-custom-tag1 -t quick-job
```


## Accessing results

In addition to using `state.result()` as described above, you can also view
results database through the `database_table` attribute (if one is available).
This returns a Simmate database object for results of ALL runs of this workflow.
Guides for filtering and manulipating the data in this table is covered in
the `simmate.database` module guides. But as an example:

``` python
table = workflow.database_table

# pandas dataframe that you can view in Spyder
df = table.obects.to_dataframe()

# or grab a specific run result and convert to a toolkit object
entry = table.objects.get(run_id="example-123456")
structure = entry.to_toolkit()
```

You'll notice the table gives results for all runs of this type (e.g. all
static-energies). To limit your results to just this specific workflow, you
can use the `all_results` property:

``` python
results = workflow.all_results

# the line above is a shortcut for...
table = workflow.database_table
results = workflow.database_table.objects.filter(workflow_name=workflow.name_full)
```

Filtering of results is covered in the `simmate.database` documentation.

<!--
TODO:
    - different documentation levels (parameters, mini docstring, etc.)
    - finding the same workflow in the website UI (place this )
-->
