
# The Supervised-Staged-Shell Workflow 

## S3 = Supervised + Staged + Shell

This type of workflow helps to **supervise** a **staged** workflow
involving some **shell** command.

Let's breakdown what this means...

A *shell* command is a single call to some external program. For example,
VASP requires that we call the "vasp_std > vasp.out" command in order to run a
calculation. We consider calling external programs a *staged* task made
up of three steps:

- setup = writing any input files required for the program
- execute = actually calling the command and running our program
- workup = loading data from output files back into python

And for *supervising* the task, this means we monitor the program while the
execution stage is running. So once a program is started, Simmate can check
output files for common errors/issues -- even while the other program is still
running. If an error is found, we stop the program, fix the issue, and then 
restart it.

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
    This diagram is slightly misleading because the "Has Errors?" check
    also happens **while the execute step is still running**. Therefore, you
    can catch errors before your program even finishes & exits!

Running S3Workflows is the same as normal workflows (e.g. using the `run` method),
and this entire process of supervising, staging, and shell execution is done for you!

----------------------------------------------------------------------

## S3Workflows for common programs

For programs that are commonly used in material science, you should also read
through their guides in the "Third-party Software" section. If your program is
listed there, then there is likely a subclass of `S3Workflow` already built 
for you. For example, VASP user can take advantage of `VaspWorkflow` to build
workflows.

----------------------------------------------------------------------

## Building a custom S3Workflow

!!! tip
    Before starting a custom `S3Workflow`, make sure you have read the section 
    above this (on S3Workflows for common programs like VASP). You should also 
    have gone through the guides on building a custom `Workflow`.


### Simple command call

The most basic example of a S3Workflow is just calling some command -- without
doing anything else (no input files, no error handling, etc.). 

Unlike custom `Workflows` were we defined a `run_config` method, `S3Workflows`
have a pre-built `run_config` method that carries out the different stages and 
monitoring of a workflow for us. So all the work is already done for us!

As an example, let's just use the command `echo` to print something:
    
``` python

from simmate.engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    use_database = False  # we aren't using a custom table for now
    monitor = False  # there is no error handling yet
    command = "echo Hello"

# behaves like a normal workflow
state = Example__Echo__SayHello.run()
result = state.result()
```

!!! tip
    Note that  we used "Echo" in our workflow name. This helps the user see what commands or programs will be called when a workflow is ran.


### Custom setup and workup

Now what if we'd like to write input files or read output files that are created?
Here, we need to update our `setup` and `workup` methods:

``` python

from simmate.engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    
    use_database = False  # we aren't using a custom table for now
    monitor = False  # there is no error handling yet

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

There are a two important things to note here:

1. It's optional to write new `setup` or `workup` methods. But if you do...
    - Both `setup` and `workup` method should be either a staticmethod or classmethod
    - Custom `setup` methods require the `directory` and `**kwargs` input parameters.
    - Custom `workup` methods require the `directory` input paramter
2. It's optional to set/overwrite attributes. You can also add new ones too.

Note: S3Workflows for a commonly used program (such `VaspWorkflow` for VASP)
will often have custom `setup` and `workup` methods already defined for you.
You can update/override these as you see fit.

For a full (and advanced) example of a subclass take a look at
`simmate.apps.vasp.workflows.base.VaspWorkflow` and the tasks that use it like
`simmate.apps.materials_project.workflows.relaxation.matproj`.


### Custom error handling

TODO -- Contact our team if you would like us to prioritize this guide

----------------------------------------------------------------------

## Alternatives to the S3Workflow

For experts, this class can be viewed as a combination of prefect's ShellTask,
a custodian Job, and Custodian monitoring. When subclassing this, we can absorb
functionality of `pymatgen.io.vasp.sets` too. By merging all of these together
into one class, we make things much easier for users and creating new Tasks.

----------------------------------------------------------------------
