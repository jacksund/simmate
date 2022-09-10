# Introduction to Python Modules

One big question still remains though: how did we know to type `from simmate.toolkit import Structure`? Here, you should learn to think of python packages (such as Simmate) as many classes and functions organized into folders. 

----------------------------------------------------------------------

## Conceptual examples

As an example, you can read `from simmate.toolkit import Structure` as "Inside of the `simmate` folder, go to the `toolkit` file and load the `Structure` class". 

Here's a second example: `from simmate.toolkit.base_data_types.lattice import Lattice` is the same as saying "Go to the `simmate` folder --> `toolkit` folder --> `base_data_types` folder --> `lattice.py` file --> grab the `Lattice` class".

So whenever you see an `import` line, it's just telling you where the actual code is located. All of Simmate's code (and all python codes everywhere) is organized like this.

----------------------------------------------------------------------

## A walk-through example

To prove it, let's go through these steps:

1. on Simmate's github homepage, go the [src/simmate folder](https://github.com/jacksund/simmate/tree/main/src/simmate) (src = source code)
2. You'll see the `toolkit` folder that we were using before.
3. Navigate through the folders. `simmate` --> `database` --> `base_data_types` --> `calculation.py`. 
4. You see a Calculation class where all of it's methods and properties are defined.

Each of these folders and files are referred to as python "modules" -- it's just python terminology.

----------------------------------------------------------------------
