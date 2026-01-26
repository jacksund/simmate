# Basic Workflow Use

------------------------------------------------------------

## List Available Workflows

=== "command line"
    ``` bash
    simmate workflows list-all
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_all_workflow_names

    names = get_all_workflow_names()
    ```

There are several more tools in `simmate.workflow.utilities` to help explore:

| utility name                 |
| ---------------------------- |
| `get_all_workflows`          |
| `get_all_workflow_names`     |
| `get_all_workflow_types`     |
| `get_apps_by_type`           |
| `get_workflow_names_by_type` |

------------------------------------------------------------

## Load a Workflow

"Loading" a workflow only applies in python. Use the `get_workflow` method, which will return the requested `Workflow` subclass:

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow_name = "static-energy.vasp.matproj"
    workflow = get_workflow(workflow_name)
    ```

------------------------------------------------------------

## View Parameters & Options

For detailed information about a specific workflow's parameters:

=== "command line"
    ``` bash
    simmate workflows explore
    ```

=== "python"
    ``` python
    workflow.show_parameters()
    ```

There are several properties & methods available for all `Workflow` subclasses:    

| property/method name       |
| -------------------------- |
| `show_parameters()`        |
| `parameter_names`          |
| `parameter_names_required` |
| `parameter_defaults`       |

!!! tip
    We've dedicated [a entire section of our documentation](/parameters.md) to workflow parameters. Please familiarize yourself with this section for detailed parameter descriptions and examples.


------------------------------------------------------------

## Run a Workflow (Local)

To execute a workflow on your local machine, use the `run` approach:

=== "yaml"
    ``` yaml
    # in example.yaml
    workflow_name: relaxation.vasp.matproj
    structure: NaCl.cif
    command: mpirun -n 8 vasp_std > vasp.out
    ```

    ``` bash
    simmate workflows run example.yaml
    ```

=== "command line"
    ``` bash
    simmate workflows run-quick relaxation.vasp.matproj --structure NaCl.cif
    ```

=== "toml"
    ``` toml
    # in example.toml
    workflow_name = "relaxation.vasp.matproj"
    structure = "NaCl.cif"
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```

    ``` bash
    simmate workflows run example.toml
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("relaxation.vasp.matproj")
    result = workflow.run(structure="NaCl.cif")
    ```

=== "website"
    ``` url
    https://simmate.org/workflows/static-energy/vasp/matproj/submit
    ```

------------------------------------------------------------

## Run a Workflow (Cloud)

Workflows can also be executed on a remote cluster. It's important to understand the differences between local and cloud runs:

=== "local (run)"
    ``` mermaid
    graph TD
      A[submit with 'run' command] --> B[starts directly on your local computer & right away];
    ```

=== "remote submission (run-cloud)"
    ``` mermaid
    graph TD
      A[submit with 'run-cloud' command] --> B[adds job to scheduler queue];
      B --> C[waits for a worker to pick up job];
      C --> D[worker selects job from queue];
      D --> E[runs the job where the worker is];
      F[launch a worker with 'start-worker' command] --> D;
    ```

To schedule a workflow to run on a remote cluster, ensure your computational resources are configured. Then, use the `run_cloud` method:

=== "command line"
    ``` yaml
    # in example.yaml
    workflow_name: static-energy.vasp.matproj
    structure: NaCl.cif
    command: mpirun -n 4 vasp_std > vasp.out
    ```
    ``` bash
    simmate workflows run-cloud example.yaml
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("static-energy.vasp.matproj")
    
    status = workflow.run_cloud(
        structure="NaCl.cif", 
        command="mpirun -n 4 vasp_std > vasp.out",
    )

    result = state.result() # (1)
    ```

    1. This will block and wait for the job to finish

!!! warning
    The `run-cloud` command/method only **schedules** the workflow. It won't 
    run until you add computational resources (or `Workers`). To do this, you
    must read through the ["Computational Resources"](/getting_started/add_computational_resources/quick_start.md) documentation.

------------------------------------------------------------

## View Workflow Results

### Option 1: Output Files

Navigate to the directory where the calculation was run to find output files (if any). Some of these include:

- `simmate_metadata.yaml`: original input parameters for the workflow run
- `simmate_summary.yaml`: a summary of information that is saved to the database
- `simmate_corrections.csv`: lists the errors encountered (if any) and how they were resolved
- *others*: for example, `relaxation` & `electronic-structure` will output plots

!!! tip
    While the plots and summary files are useful for quick viewing, there is much 
    more information available in the database.

### Option 2: Python Objects

Access the result directly in python. Workflows can return `any` - however, workflows that save to a database table will return the actual database object. 

=== "python"
    ``` python 
    result = workflow.run(...) # (1)
    ```

    1. Returns a `Database` object. In some cases, you can convert to a `toolkit` structure using `result.to_toolkit()`

For viewing the results of *many* workflow runs:

=== "python"
    ``` python
    results = workflow.all_results  # (1)
    ```

    1. This takes the relevent table (e.g. `StaticEnergy`) and filters down to all results matching this workflow name.

!!! tip
    View the [Database](/full_guides/database/basic_use.md) guides for advanced filtering and data manipulation.

### Option 3: The Database

You can view the data directly via SQL. For example:

=== "SQL"
    ``` postgres
    SELECT *
    FROM workflows_staticenergy
    WHERE workflow_name = 'static-energy.vasp.mit'
    ```

!!! tip
    We recommend exploring database tables using [DBeaver](https://dbeaver.io/)

### Option 4: The Website Server

!!! warning
    this is an experimental feature and still in early development

In the `simmate_summary.yaml` output file, there is the `_WEBSITE_URL_`. You can copy/paste this URL into your browser and view your results in an interactive format. Just make sure you are running your local server first:

``` shell
simmate run-server
```

Then open the link given by `_WEBSITE_URL_`:

```
http://127.0.0.1:8000/workflows/static-energy/vasp/mit/1
```

------------------------------------------------------------

## Run Massively Parallel Workflows

Some workflows submit many subworkflows. For example, evolutionary structure prediction does this by submitting hundreds of individual structure relaxations, analyzing the results, and submitting new structures based on the results.

This is achieved by the workflow manually calling `run-cloud` on others. If you start multiple workers elsewhere, you can calculate these subworkflows in parallel:

``` mermaid
graph TD
  A[main workflow];
  A --> B[subworkflow];
  B --> C[schedule run 1] --> G[scheduler];
  B --> D[schedule run 2] --> G;
  B --> E[schedule run 3] --> G;
  B --> F[schedule run 4] --> G;
  G --> H[worker 1];
  G --> I[worker 2];
  G --> J[worker 3];
```

To run these types of workflows, you must:

1. Start the main workflow with the `run` command
2. Start at least one worker that will run the submitted calculations
    
!!! note
    The number of workers will determine how many jobs are run in parallel -- and this
    is only limited by the number of jobs queued. For example, if I submit 500
    workflows with `run-cloud` but only start 100 workers, then only 100 workflows
    will be run at a time. Further, if I submit 25 workflows but have 100 workers,
    then that means 75 of our workflows will be sitting idle without any job
    to run.

------------------------------------------------------------
