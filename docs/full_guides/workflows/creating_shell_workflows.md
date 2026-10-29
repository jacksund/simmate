# Overview of Shell Workflows

### What is a `ShellWorkflow`?

A `ShellWorkflow` runs an external program through a shell command. It involves writing input files, calling the program, and reading the output files. Each run has three stages (each is a class method):

1. `setup` = write input files
2. `execute` = run the program's shell command and monitor it for errors in the background
3. `workup` = read the output files

Together, the `run` method of a `ShellWorkflow` carries out the following:

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

## Creating ShellWorkflows

For commonly used material science programs, refer to their guides in the "Third-party Software" section. If your program is listed there, a subclass of `ShellWorkflow` is likely already available. For instance, VASP users can use `VaspWorkflow` to build workflows.

## Building a Custom ShellWorkflow

!!! tip
    Before creating a custom `ShellWorkflow`, ensure you've read the section on ShellWorkflows for common programs like VASP and the guides on building a custom `Workflow`.

### Simple Command Call

The simplest example of a ShellWorkflow is a single command call without any additional actions (no input files, no error handling, etc.). 

Unlike custom `Workflows` where we define a `run_config` method, `ShellWorkflows` have a pre-built `run_config` method that handles the different stages and monitoring of a workflow. 

For instance, let's use the `echo` command to print something:

``` python
from simmate.workflows.common import ShellWorkflow

class Example__Echo__SayHello(ShellWorkflow):
    monitor = False  # no error handling yet
    command = "echo Hello"

# behaves like a normal workflow
result = Example__Echo__SayHello.run()
```

!!! tip
    Note the use of "Echo" in our workflow name. This helps users understand what commands or programs will be run when a workflow is executed.

### Custom Setup and Workup

If you need to write input files or read output files, you'll need to update your `setup` and `workup` methods:

``` python
from simmate.workflows.common import ShellWorkflow

class Example__Echo__SayHello(ShellWorkflow):
    
    monitor = False  # no error handling yet

    command = "echo Hello > output.txt"  # adds "Hello" into a new file

    @classmethod
    def setup(cls, directory, custom_parameter, **kwargs):
        # The directory given is a pathlib.Path object for the directory
        # that the command will be called in
        
        print("I'm setting things up!")
        print(f"My new setting value is {cls.some_new_setting}")
        print(f"My new parameter value is {custom_parameter}")
        
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

ShellWorkflows for commonly used programs (like `VaspWorkflow` for VASP) often have custom `setup` and `workup` methods already defined. You can modify these as needed.

For a comprehensive example of a subclass, refer to `simmate.apps.vasp.workflows.base.VaspWorkflow` and the tasks that use it like `simmate.apps.materials_project.workflows.relaxation.matproj`.

### Custom Error Handling

`ShellWorkflows` can automatically detect and fix errors that occur during the `execute` stage. This is done using `ErrorHandler` objects.

To add error handling to your workflow:

1. Define one or more `ErrorHandler` classes.
2. Add them to the `error_handlers` attribute of your workflow.

#### Creating an Error Handler

An `ErrorHandler` needs to define:

- `check`: A method that returns `True` if an error is detected.
- `correct`: A method that performs corrective actions (e.g., modifying input files).

``` python
from simmate.workflows.core import ErrorHandler

class MyCustomHandler(ErrorHandler):
    
    # Files to check and messages to look for
    filename_to_check = "vasp.out"
    possible_error_messages = ["Internal error: Segmentation fault"]

    def correct(self, directory):
        # This method is called if `check` returns True.
        # We can modify files in the directory to fix the error.
        incar_file = directory / "INCAR"
        # ... logic to modify INCAR ...
        return "Applied fix for segmentation fault"
```

#### Using Error Handlers in a Workflow

``` python
class Relaxation__Vasp__MyExample(VaspWorkflow):
    
    error_handlers = [MyCustomHandler]
    
    # ... other settings ...
```

#### Monitoring During Execution

By default, error handlers are checked after the command finishes. However, some errors can be caught *while the program is still running*. To enable this, set `is_monitor = True` on your handler:

``` python
class MyMonitorHandler(ErrorHandler):
    is_monitor = True
    # ... check and correct methods ...
```

When a monitor handler detects an error, Simmate will terminate the running process, apply the fix, and restart the calculation.

!!! tip
    Monitoring is extremely useful for catching non-converging calculations or other issues that would otherwise waste hours of CPU time.

## Alternatives to ShellWorkflow

For advanced users, the ShellWorkflow class combines the functionality of Prefect's ShellTask, a Custodian Job, and Custodian monitoring. When subclassing this, we can also incorporate functionality from `pymatgen.io.vasp.sets`. By merging these into one class, we simplify the process for users and task creation.