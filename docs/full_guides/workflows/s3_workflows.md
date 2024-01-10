# Overview of Supervised-Staged-Shell Workflow

## Introduction to S3: Supervised, Staged, Shell

The S3 workflow is designed to **supervise** a **staged** workflow that involves a **shell** command.

A *shell* command is a single call to an external program. For example, the "vasp_std > vasp.out" command is used to run a calculation in VASP. This call is considered a *staged* task, which includes three steps:

- Setup: Writing necessary input files for the program.
- Execute: Running the program by calling the command.
- Workup: Loading data from output files back into Python.

*Supervising* the task involves monitoring the program during the execution stage. Simmate can check output files for common errors or issues while the program is running. If an error is detected, the program is stopped, the issue is fixed, and the program is restarted.

``` mermaid
graph LR
  A[Start] --> B[setup];
  B --> C[execute];
  C --> D[workup];
  D --> E[Has errors?];
  E -->|Yes| B;
  E -->|No| F[Done!];
```

!!! warning
    The diagram is slightly misleading as the "Has Errors?" check also occurs **while the execute step is still running**. This allows for early error detection before the program completes its run.

Running S3Workflows is similar to running normal workflows (e.g., using the `run` method), and the entire process of supervision, staging, and shell execution is automated.

## Implementing S3Workflows with Common Programs

For commonly used material science programs, refer to their guides in the "Third-party Software" section. If your program is listed there, a subclass of `S3Workflow` is likely already available. For instance, VASP users can use `VaspWorkflow` to build workflows.

## Building a Custom S3Workflow

!!! tip
    Before creating a custom `S3Workflow`, ensure you've read the section on S3Workflows for common programs like VASP and the guides on building a custom `Workflow`.

### Simple Command Call

The simplest example of an S3Workflow is a single command call without any additional actions (no input files, no error handling, etc.). 

Unlike custom `Workflows` where we define a `run_config` method, `S3Workflows` have a pre-built `run_config` method that handles the different stages and monitoring of a workflow. 

For instance, let's use the `echo` command to print something:

``` python
from simmate.engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    use_database = False  # no custom table for now
    monitor = False  # no error handling yet
    command = "echo Hello"

# behaves like a normal workflow
state = Example__Echo__SayHello.run()
result = state.result()
```

!!! tip
    Note the use of "Echo" in our workflow name. This helps users understand what commands or programs will be run when a workflow is executed.

### Custom Setup and Workup

If you need to write input files or read output files, you'll need to update your `setup` and `workup` methods:

``` python
from simmate.engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    
    use_database = False  # no custom table for now
    monitor = False  # no error handling yet

    command = "echo Hello > output.txt"  # adds "Hello" into a new file

    @classmethod
    def setup(cls, directory, custom_parameter, **kwargs):
        # The directory given is a pathlib.Path object for the directory
        # that the command will be called in
        
        print("I'm setting things up!")
        print(f"My new setting value is {cls.some_new_setting}")
        print(f"My new parameter value is {custom_parmeter}")
        
        return  # no need to return anything. Nothing will be done with it.

    @staticmethod
    def workup(directory):
        # The directory given is a pathlib.Path object for the directory
        # that the command will be called in
        
        # Simply check that we have a new file
        output_file = directory / "output.txt"
        assert output_file.exists()
        
        print("I'm working things up!")
        return "Done!"

task = Example__Echo__SayHello()
result = task.run()
```

Note:

1. Writing new `setup` or `workup` methods is optional. If you do...
    - Both `setup` and `workup` methods should be either a staticmethod or classmethod.
    - Custom `setup` methods require the `directory` and `**kwargs` input parameters.
    - Custom `workup` methods require the `directory` input parameter.
2. Setting/overwriting attributes is optional. You can also add new ones.

S3Workflows for commonly used programs (like `VaspWorkflow` for VASP) often have custom `setup` and `workup` methods already defined. You can modify these as needed.

For a comprehensive example of a subclass, refer to `simmate.apps.vasp.workflows.base.VaspWorkflow` and the tasks that use it like `simmate.apps.materials_project.workflows.relaxation.matproj`.

### Custom Error Handling

Custom error handling is currently under development. Please contact our team if you need this guide prioritized.

## Alternatives to S3Workflow

For advanced users, the S3Workflow class combines the functionality of Prefect's ShellTask, a Custodian Job, and Custodian monitoring. When subclassing this, we can also incorporate functionality from `pymatgen.io.vasp.sets`. By merging these into one class, we simplify the process for users and task creation.