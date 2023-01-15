
# The full Simmate guides & API reference


## Before you begin

To get started, make sure you have either completed our [introductory tutorials](/getting_started/overview/) or are comfortable with python.

------------------------------------------------------------

## Organization of guides vs. code

Though we try to keep the organization of our guides and code as close as possible, they do not exactly follow the same structure. We learned over time that code/guide organization needs to be handled separately to help new users begin using Simmate without having mastered all of it components.

### documentation

We try to organize our guides in order of progressing difficulty. This also matches the way in which most users will begin to work with Simmate&mdash;namely, beginning with the highest-level features (the website interface) and progressing towards the lowest-level features (the toolkit and python objects). The documentation therefore proceeds in the following sequence.

``` mermaid
graph LR
  A[Website] --> B[Workflows];
  B --> C[Database];
  C --> D[Toolkit];
  D --> E[Extras];
```

!!! tip
    Advanced topics are located at the end of each section. Unlike the 
    getting-started guides, you do **not** need to complete a section in order 
    to move on to the next one.

### python modules

`simmate` is the base module and contains all of the code that our package runs on. Within each subfolder (i.e., each python “module”), you’ll find more details on its contents.

These modules are:

- `apps` = each runs a specific analysis or third-party program (e.g., VASP, which runs DFT calculations)
- `command_line` = common functions that are available as commands in the terminal
- `configuration` = default Simmate settings and methods to change them
- `database` = defines the structure of data tables and the methods to access the tables
- `file_converters` = methods to convert between filetypes (e.g., POSCAR to CIF)
- `toolkit` = core methods and classes for Simmate (e.g. the `Structure` class)
- `utilities` = simple functions that are used throughout other modules
- `visualization` = methods to visualize structures and data
- `website` = runs the simmate.org website
- `workflow_engine` = tools that run calculations and handle errors
- `workflows` = tools that define each calculation type (e.g., a structure optimization)

There is also one extra file…

- `conftest` = this runs Simmate tests and is only for contributing devs

------------------------------------------------------------
