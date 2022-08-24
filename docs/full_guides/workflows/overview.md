# Simmate Workflows

This module brings together all predefined workflows and organizes them by application for convenience.

This module covers basic use, but more information is available in `simmate.workflow_engine.workflow`.


# Basic use

[Tutorials 01-05](https://github.com/jacksund/simmate/tree/main/tutorials) will teach you how to run workflows and access their results. But as a review:

``` python
from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj as workflow

# runs the workflow and returns a state
state = workflow.run(structure="my_structure.cif")
result = state.result()

# gives the DatabaseTable where ALL results are stored
workflow.database_table  # --> gives all relaxation results
workflow.all_results  # --> gives all results for this relaxation preset
df = workflow.all_results.to_dataframe()  # convert to pandas dataframe
```

Further information on interacting with workflows can be found in the `simmate.workflow_engine` module as well -- particularly, the `simmate.workflow_engine.workflow` module.


# Avoiding long import paths

If you are a regular python user, you'll notice the import path above is long and unfriendly. If you'd like to avoid importing this way, you can instead use the `get_workflow` utility:

``` python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.matproj")
```


# Workflow naming conventions

All workflow names follow a specific format of `Type__Calculator__Preset` so for an example workflow like `StaticEnergy__Vasp__Matproj` this means that...

- Type = StaticEnergy (workflow runs a single point energy)
- Calculator = Vasp  (workflow uses VASP to calculate the energy)
- Preset = Matproj  (workflow uses "Matproj" type settings in the calculation)

The workflow name can also be used to infer where the workflow is located in python. For `StaticEnergy__Vasp__Matproj`, this corresponds to a name of `static-energy.vasp.matproj` and means the workflow can be accessed in the following ways:

1. `from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj` (uses the `type`)
2. `from simmate.calculators.vasp.workflows.static_energy.all import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator`)
3. `from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator` and `preset`)

These imports all give the same workflow, but we recommend stick to the first option because it is the most convienent and easiest to remember. The only reason you'll need to interact with the other options is to either:

1. Find the source code for a workflow (see section below for more)
2. Optimize the speed of your imports (advanced users only)


<!--
# Location of a workflow in the website interface

You can follow the naming conventions (described above) to find a workflow in the website interface:

```
# Template to use for finding workflows
https://simmate.org/workflows/{TYPE}/{CALCULATOR}/{PRESET}

# Example with StaticEnergy__Vasp__Matproj
https://simmate.org/workflows/static-energy/vasp/matproj
```
-->


# Location of a workflow's source code

The code that defines these workflows and configures their settings are located in the corresponding `simmate.calculators` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. The source code of a workflow can be found using the naming convention for workflows described above:

``` python
# Template to use for finding workflows
from simmate.calculators.{CALCULATOR}.workflows.{TYPE}.{PRESET} import {FULL_NAME}

# Example with StaticEnergy__Vasp__Matproj
from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj
```

# The Simmate Workflow Engine


This module defines common workflows, error handling, and submission/running of workflows. It is ment for users that want to create custom workflows from scratch. Use of this module is closely tied with [Tutorials 06 and 09](https://github.com/jacksund/simmate/tree/main/tutorials).

This module is only meant for advanced users. Beginners should instead start by checking if there is already a workflow built for them (in `simmate.workflows`) or by checking if there are common base workflows already built for the program they are using in `simmate.calculators`. For example, VASP users can check `simmate.calculators.vasp.workflows`.


# Overview of classes

Here we try to give a birds-eye view of Simmate workflows and a commonly used subclass known as a "s3 workflow". This section is not meant to be an encompassing guide. Instead, beginners should refer to our tutorials and class-level API docs.


## What is a `Workflow`?

Recall from Simmate's [tutorial 02](https://github.com/jacksund/simmate/blob/main/tutorials/02_Run_a_workflow.md), that a `Workflow` is made up of 4 stages:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. VASP), and checks the results for errors
- `save`: saves the results to our database

The `configure` step is simply how a workflow is defined. Pre-built workflows do this for you already, but you may want to create a custom workflow for more. By creating a new `Workflow` subclass, you've configured it.

The `schedule` step is handled entirely by Simmate. All that you need to know is that `run` will carry out the workflow on your local computer, while `run_cloud` will schedule the workflow to run remotely.

The `execute` step is what we typically think of when we think "workflow". It can be anything and everything. The example given (writing inputs, calling a program, and reading output files) is the most common type of workflow in Simmate -- known as a "S3Workflow". This is explained more below.

The `save` step is simply taking the result of the `execute` and saving it to a SQL database. This is handled automatically for common workflows types like relaxations, dynamics, or static-energy calculations, but advanced users may want to customize their own methods.

All stages of a `Workflow` are done through the `run` or `run_cloud` methods. That is... `Workflow.run` = `configure` + `schedule` + `execute` + `save`.

To begin building custom workflows, make sure you have completed [tutorial 06](https://github.com/jacksund/simmate/blob/main/tutorials/06_Build_custom_workflows.md) and then read through the `simmate.workflow_engine.workflow` documentation.


## What is a `NestedWorkflow`?

Some workflows are "nested", which means it's a workflow made up multiple other workflows. An example of this is the `relaxation.vasp.staged` workflow, which involves a series of relaxations of increasing quality and then a final energy calculation.


## What is an `S3Workflow`?

Many workflows involve writing input files, calling some external program, and then reading through the output files. All workflows like this are known as "`S3Workflow`"s. S3 means the workflow is **Supervised**, **Staged**, and a **Shell** call. For shorthand, we call this a "S3" workflow. There is some history behind why it's named this way, but here is how the name breaks down:

- `Staged`: the overall calculation is made of three stages (each is a class method)
    1. `setup` = write input files
    2. `run_command_and_monitor` = the actual running & monitoring of the program
    3. `workup` = reading the output files
- `Shell`: the calculator is called through the command-line (the actual `execution` call)
- `Supervised`: once the shell command is started, Simmate runs in the background to monitor it for errors (occurs during the `execution` call)

All stages of this S3 workflow are packed into the `excute` step of a `Workflow`, where Simmate has a lot of functionality built for you already.

If you would like to build a custom S3 workflow, we suggest going through:
1. [tutorial 06](https://github.com/jacksund/simmate/blob/main/tutorials/06_Build_custom_workflows.md)
2. `simmate.workflow_engine.workflow` documentation
3. `simmate.workflow_engine.s3_workflow` documentation

