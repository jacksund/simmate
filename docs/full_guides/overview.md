
# The full Simmate guides & API reference

## Before you begin

To get started, make sure you have either completed our [introduction tutorials](https://github.com/jacksund/simmate/tree/main/tutorials)
or are comfortable with python.


## Organization of guides vs. code

Though we try to keep the organization of our guides and code as close as possible, they do not exactly follow the same structure. We learned over time that code vs. guide organization needs to be handled separately -- in order to help new users learn how to use Simmate.

### documentation

- TODO

### python modules

`simmate` is the base module and contains all of the code that our package runs on. Within each subfolder (aka each python “module”), you’ll find more details on what it contains.

But as a brief summary...

- `calculators` = third-party programs that run analyses for us (e.g. VASP which runs DFT calculations)
- `command_line` = makes some common functions available as commands in the terminal
- `configuration` = the defualt Simmate settings and how to update them 
- `database` = defines how all Simmate data is organized into tables and let’s you access it 
- `file_converters` = reformat to/from file types (e.g. POSCAR –> CIF)
- `toolkit` = the fundamental functions and classes for Simmate (e.g. the `Structure` class)
- `utilities` = contains simple functions that are used throughout the other modules
- `visualization` = visualizing structures, 3D data, and simple plots
- `website` = runs the simmate.org website 
- `workflow_engine` = tools and utilities that help submit calculations as well as handle errors
- `workflows` = common analyses used in materials chemistry

There is also one extra file…

- `conftest` = this is for running Simmate tests and only for contributing devs


