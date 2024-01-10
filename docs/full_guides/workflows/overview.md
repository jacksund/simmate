# Simmate Workflows Module

This module organizes all predefined workflows by application for easy access.

While this module provides basic usage, you can find more information in `simmate.engine.workflow`.

## Basic Usage

[The getting-started tutorials](/simmate/getting_started/overview/) offer detailed instructions on running workflows and retrieving their results. Here's a brief summary:

``` python
from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj as workflow

# Run the workflow and return a state
state = workflow.run(structure="my_structure.cif")
result = state.result()

# Access the DatabaseTable where ALL results are stored
workflow.database_table  # --> returns all relaxation results
workflow.all_results  # --> returns all results for this relaxation preset
df = workflow.all_results.to_dataframe()  # convert to pandas dataframe
```

For more details on interacting with workflows, refer to the `simmate.engine` module, specifically the `simmate.engine.workflow` module.

## Simplifying Import Paths

The import path above may seem lengthy and complex, especially for regular python users. To simplify this, you can use the `get_workflow` utility:

``` python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.matproj")
```

## Overview of Classes

### What is a `Workflow`?

As explained in Simmate's [getting-started tutorial](/simmate/getting_started/run_a_workflow/stages_of_a_workflow/), a `Workflow` consists of 4 stages:

- `configure`: Sets the calculation settings (like VASP's INCAR settings)
- `schedule`: Determines whether to run the workflow immediately or queue it for later (e.g., SLURM, PBS, or remote computers)
- `execute`: Writes input files, runs the calculation (e.g., VASP), and checks the results for errors
- `save`: Stores the results in our database

The `configure` step defines a workflow. Pre-built workflows are already configured, but you can create a custom workflow for more flexibility. 

The `schedule` step is managed by Simmate. You only need to know that `run` executes the workflow on your local computer, while `run_cloud` schedules it to run remotely.

The `execute` step is the core of the workflow. It can include various tasks. The most common type of workflow in Simmate, known as a "S3Workflow", is explained below.

The `save` step takes the result of the `execute` step and saves it to a SQL database. This is automated for common workflows like relaxations, dynamics, or static-energy calculations. However, advanced users may want to customize their methods.

All stages of a `Workflow` are executed through the `run` or `run_cloud` methods. In other words, `Workflow.run` = `configure` + `schedule` + `execute` + `save`.

To start building custom workflows, complete [the getting-started tutorials](/simmate/getting_started/) and review the `simmate.engine.workflow` documentation.

### What is a `NestedWorkflow`?

A "nested" workflow is a workflow composed of multiple other workflows. For instance, the `relaxation.vasp.staged` workflow includes a series of relaxations of increasing quality followed by a final energy calculation.

### What is an `S3Workflow`?

An `S3Workflow` involves writing input files, calling an external program, and reading the output files. The term "S3" stands for **Supervised**, **Staged**, and **Shell** call. Here's what each term means:

- `Staged`: The calculation consists of three stages (each is a class method)
    1. `setup` = write input files
    2. `run_command_and_monitor` = run & monitor the program
    3. `workup` = read the output files
- `Shell`: The program is called through the command-line (the actual `execution` call)
- `Supervised`: Simmate monitors the shell command for errors in the background (occurs during the `execution` call)

All stages of an S3 workflow are included in the `execute` step of a `Workflow`, where Simmate provides extensive built-in functionality.

To build a custom S3 workflow, we recommend going through:
1. [getting-started guides](/simmate/getting_started/overview/)
2. `simmate.engine.workflow` documentation
3. `simmate.engine.s3_workflow` documentation