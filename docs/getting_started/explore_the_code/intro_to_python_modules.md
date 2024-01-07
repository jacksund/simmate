# Introduction to Python Modules

A key question to address is: how do we know to type `from simmate.toolkit import Structure`? To understand this, it's important to view Python packages (like Simmate) as a collection of classes and functions neatly organized into directories. 

----------------------------------------------------------------------

## Conceptual examples

For instance, the command `from simmate.toolkit import Structure` can be interpreted as "Navigate to the `simmate` directory, access the `toolkit` file, and load the `Structure` class". 

Here's another example: `from simmate.toolkit.base_data_types.lattice import Lattice` essentially means "Navigate to the `simmate` directory --> `toolkit` directory --> `base_data_types` directory --> `lattice.py` file, and then load the `Lattice` class".

In essence, an `import` line is simply a guide to the location of the actual code. This is the standard organization for Simmate's code, as well as Python codes universally.

----------------------------------------------------------------------

## A walk-through example

To illustrate this, let's follow these steps:

1. Visit Simmate's GitHub homepage and navigate to the [src/simmate directory](https://github.com/jacksund/simmate/tree/main/src/simmate) (src = source code).
2. Here, you'll find the `toolkit` directory that we previously used.
3. Continue navigating through the directories: `simmate` --> `database` --> `base_data_types` --> `calculation.py`. 
4. Here, you'll find a Calculation class with all its methods and properties defined.

Each of these directories and files are referred to as Python "modules" -- a term specific to Python.

----------------------------------------------------------------------