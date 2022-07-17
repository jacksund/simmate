# The Simmate Workflow Engine


This module defines common workflow tasks, error handling, and job restarts. It is ment for users that want to create custom workflows from scratch. Use of this module is closely tied with [Tutorials 08](https://github.com/jacksund/simmate/tree/main/tutorials).

This module is only meant for advanced users. Beginners should instead start by checking if there is already a workflow built for them (in `simmate.workflows`) or by checking if there are common tasks already built for the program they are using in `simmate.calculators`. For example, VASP users can check `simmate.calculators.vasp`.


# Overview of classes

Here we try to give a birds-eye view of how Simmate `Tasks`, `DatabaseTables`, and `Workflows` fit together. This section is not meant to be an encompassing guide. Instead, beginners should refer to our tutorials and class-level API docs.


## What is an `S3Task`?

A single calculator run is carried out by a `StagedSupervisedShellTask` or a "`S3Task`". There is some history behind why it's named this way, but here is how the name breaks down:

- `Staged`: the overall calculation is made of three stages (each is a class method)
    1. `setup` = write input files
    2. `execution` = the actual running & monitoring of the program  <--- `Supervised` and `Shell` help describe this stage
    3. `workup` = reading the output files
- `Shell`: the calculator is called through the command-line
- `Supervised`: once the shell command is started, Simmate runs in the background to monitor it for errors

All stages of an `S3Task` are done through the `run` method. That is... `S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`


## What is a `Workflow`?

Recall from Simmate's [tutorial 2](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md), that a `Workflow` is made up of 4 stages. These stages can be thought of linking a `S3Task` and a `DatabaseTable`:

- `configure`: default settings are attached to `S3Task`'s attribute
- `schedule`: decides when and where `S3Task.run` is called
- `execute`: calls `S3Task.run` which does setup (`S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`)
- `save`: takes the output of `S3Task` and saves it to the `DatabaseTable`

All stages of a `Workflow` are done through the `run` method. That is... `Workflow.run` = `configure` + `schedule` + `execute` + `save`.


## What is a `NestedWorkflow`?

Some workflows are "nested", which means it's a workflow made up multiple other workflows. An example of this is the `relaxation.vasp.staged` workflow, which involves a series of relaxations of increasing quality and then a final energy calculation.
