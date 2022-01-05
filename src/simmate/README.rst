
Welcome to Simmate!
-------------------

This module contains all of the code that Simmate runs on. To get started, make sure
you have either completed our `introduction tutorials`_ or are comfortable with python.

Within each subfolder (aka each python “module”), you’ll find more details on what it contains.

**But as a brief summary…**

- ``calculators`` = third-party programs that run analyses for us (e.g. VASP which runs DFT calculations)
- ``command_line`` = makes some common functions available as commands in the terminal (for advanced users) 
- ``configuration`` = the defualt Simmate settings and how to update them 
- ``database`` = defines how all Simmate data is organized into tables (aka “models”) and let’s you access it 
- ``file_converters`` = reformat to/from file types (e.g. POSCAR –> CIF) 
- ``toolkit`` = “core” functions for Simmate, ranging from pulling out symmetry to transforming a crystal lattice
- ``visualization`` = visualizing structures, 3D data, and simple plots
- ``website`` = runs the simmate.org website 
- ``workflow_engine`` = tools and utilities that help submit calculations as well as handle errors
- ``workflows`` = common analyses used in materials chemistry

**There are also two extra files…** 

- ``shortcuts`` = let’s you import common functions with ease 
- ``utilities`` = contains simple functions that are used throughout the other modules

.. _introduction tutorials: https://github.com/jacksund/simmate/tree/main/tutorials
