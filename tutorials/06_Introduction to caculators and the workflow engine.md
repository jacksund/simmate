# Introduction to caculators and the workflow engine

> :warning: This tutorial isn't required for beginners to use Simmate. Instead, this helps you understand what Simmate is doing behind the scenes. If you'd like to create custom workflows or contribute to Simmate, then understanding these core concepts is the place to start.

# The quick tutorial



# The full tutorial

### What is a `calculator`?

A `Calculator` is an external program that Simmate calls in order to run a calculation (e.g. [VASP](https://vasp.at/), [ABINIT](https://www.abinit.org/), [bader](http://theory.cm.utexas.edu/henkelman/code/bader/), etc.) and the `simmate.calculators` module stores all of the code for input/outputs, common error handlers, and more.

### What is an `S3Task`?

A single calculator run is carried out by a `StagedSupervisedShellTask` or a "`S3Task`". There is some history behind why it's named this way, but here is how the name breaks down:

- `Staged`: the overall calculation is made of three stages (each is a class method)
    1. `setup` = write input files
    2. `execution` = the actual running & monitoring of the program  <--- `Supervised` and `Shell` help describe this stage
    3. `workup` = reading the output files
- `Shell`: the calculator is called through the command-line
- `Supervised`: once the shell command is started, Simmate runs in the background to monitor it for errors

All stages of an `S3Task` are done through the `run` method. That is... `S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`

### What is a `Workflow`?

Recall from tutorial 2, that a `Workflow` is made up of 4 stages. These stages can be thought of linking a `S3Task` and a `DatabaseTable`:

- `configure`: default settings are attached to `S3Task`'s attribute
- `schedule`: decides when and where `S3Task.run` is called
- `execute`: calls `S3Task.run` which does setup (`S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`)
- `save`: takes the output of `S3Task` and saves it to the `DatabaseTable`

All stages of a `Workflow` are done through the `run` method. That is... `Workflow.run` = `configure` + `schedule` + `execute` + `save`.

### What is a `NestedWorkflow`?

Some workflows are "nested", which means it's a workflow made up other multiple other workflows. An example of this is the `relaxation_staged` workflow, which involves a series of relaxations of increasing quality and then a final energy calculation.

6. Feel free to add a calculator for a new program if you don't see it in [the available list](https://github.com/jacksund/simmate/tree/main/src/simmate/calculators)!

# The full tutorial

