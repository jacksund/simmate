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
