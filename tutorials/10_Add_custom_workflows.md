:warning::warning::warning: THIS TUTORIAL IS INCOMPLETE AT THE MOMENT :warning::warning::warning:

# Introduction to caculators and the workflow engine

> :warning: This tutorial isn't required for beginners to use Simmate. Instead, this helps you understand what Simmate is doing behind the scenes. If you'd like to create custom workflows or contribute to Simmate, then understanding these core concepts is the place to start.

# The quick tutorial

1. If you'd like to see what third-party programs Simmate supports, take a look at the `simmate.calculators` module ([here](https://github.com/jacksund/simmate/tree/main/src/simmate/calculators))

2. Each call to a program is considered a single task. These tasks all inherit from a `S3Task` class and implement their own `setup`, `execute`, and `workup` methods. Here's what top-level usage looks like for [VASP](https://vasp.at/):

```python
from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS_LOW_QUALITY

class ExampleRelaxation(VaspTask):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY
    incar = dict(
        PREC="Low",
        EDIFF=2e-3,
        EDIFFG=-2e-1,
        NSW=75,
        IBRION=2,
        POTIM=0.02,
        KSPACING=0.75,
    )
 
my_task = ExampleRelaxation()
result = my_task.run()  # calls the setup, execute, and workup methods for us
```

3. Workflows add orchestration and database saving to the `S3Task`. The simplest workflows are just one call to a calculator:

```python
from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation.example import ExampleRelaxationTask
from simmate.calculators.vasp.database.example import ExampleRelaxationResults

workflow = s3task_to_workflow(
    name="Quality 00 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=ExampleRelaxationTask,
    calculation_table=Quality00RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)

result = workflow.run(structure=structure)  # now includes saving results to a database table!
```

*note: we keep `S3Task`'s and `Workflows` separate to for modularity of our code*

4. Make a custom `S3task` whenever you want to test out new calculations. Results won't be saved to your database. When you're ready to start storing data from your tasks, ... TODO need to combine this tutorial with custom apps




# The full tutorial

## What is a `calculator`?

A `Calculator` is an external program that Simmate calls in order to run a calculation (e.g. [VASP](https://vasp.at/), [ABINIT](https://www.abinit.org/), [bader](http://theory.cm.utexas.edu/henkelman/code/bader/), etc.) and the `simmate.calculators` module stores all of the code for input/outputs, common error handlers, and more.

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

Recall from tutorial 2, that a `Workflow` is made up of 4 stages. These stages can be thought of linking a `S3Task` and a `DatabaseTable`:

- `configure`: default settings are attached to `S3Task`'s attribute
- `schedule`: decides when and where `S3Task.run` is called
- `execute`: calls `S3Task.run` which does setup (`S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`)
- `save`: takes the output of `S3Task` and saves it to the `DatabaseTable`

All stages of a `Workflow` are done through the `run` method. That is... `Workflow.run` = `configure` + `schedule` + `execute` + `save`.

## What is a `NestedWorkflow`?

Some workflows are "nested", which means it's a workflow made up other multiple other workflows. An example of this is the `relaxation_staged` workflow, which involves a series of relaxations of increasing quality and then a final energy calculation.

6. Feel free to add a calculator for a new program if you don't see it in [the available list](https://github.com/jacksund/simmate/tree/main/src/simmate/calculators)!

# The full tutorial

