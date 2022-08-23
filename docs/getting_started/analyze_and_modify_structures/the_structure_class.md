
# The `Structure` class

In real life, we might say that McDonald's, Burger King, and Wendy's are examples of restauraunts.  In python, we could say that `mcdonalds`, `burgerking`, and `wendys` are **objects** of the **class** `Restaurants`.  By organizing **objects** into **class**es, python simplifies the way we program. For example, we could design the `Restaurants` class to have a property called `menu`.  Then, we could view the menu simply by typing `wendys.menu` because `wendys` belongs to the **class** `Restaraunts` and all `Restaraunts` have a `menu`.

In materials science, the class we use most is crystal structure. In Simmate, we call this class `Structure`. A crystal structure is _**always**_ made up of a lattice and a list of atomic sites. Fortunately, this is exactly what we have in our `POSCAR` file from tutorial 2, so let's use Simmate to create an instance of the `Structure` class using our POSCAR file.

Start by entering this line into the python console and hit enter:

```python
from simmate.toolkit import Structure
```

This line says we want to use the `Structure` class from Simmate's code. The `Structure` class is now loaded into memory and is waiting for you to do something with it.

Next, make sure you have the correct working directory (just like we did with the command-line). Spyder lists this in the top right -- and you can hit the folder icon to change it. We want to be in the same folder as our POSCAR file.

Next, run this line in your python terminal:

```python
nacl_structure = Structure.from_file("POSCAR")
```

Here, we told python that we have a `Structure` and the information for it is located in the `POSCAR` file. This could be in many other formats, such as a CIF file. But we now have a `Structure` object and it is named `nacl_structure`. To make sure it loaded correctly, run this line:

```python
nacl_structure
```

It should print out...

```
Structure Summary
Lattice
    abc : 4.02463542 4.02463542 4.02463542
 angles : 59.99999999999999 59.99999999999999 59.99999999999999
 volume : 46.09614820053437
      A : 3.4854365146906536 0.0 2.0123177100000005
      B : 1.1618121715635514 3.2861010599106226 2.0123177100000005
      C : 0.0 0.0 4.02463542
PeriodicSite: Na (0.0000, 0.0000, 0.0000) [0.0000, 0.0000, 0.0000]
PeriodicSite: Cl (2.3236, 1.6431, 4.0246) [0.5000, 0.5000, 0.5000]
```

This is the same information from our POSCAR! Alternatively, we could have created this structure manually:

```python
# note we can name the object whatever we want. We use 's' here.
s = Structure(
    lattice=[
        [3.48543651, 0.0, 2.01231771],
        [1.16181217, 3.28610106, 2.01231771],
        [0.0, 0.0, 4.02463542],
    ],
    species=["Na", "Cl"],
    coords=[
        [0.0000, 0.0000, 0.0000],
        [0.5000, 0.5000, 0.5000],
    ],
)
```

Whatever your method for creating a structure, we now have our `Structure` object and we can use its properties (and methods) to simplify our calculations.

For example, we can use it to run a workflow. We did this with the command-line in the last tutorial but can accomplish the same thing with python:

``` shell
# Using the command-line (from our previous tutorial)
simmate workflows run static-energy/mit --structure POSCAR
```

```python
# Using Python (in Spyder)

# This code does the exact same thing as the command above

from simmate.toolkit import Structure
from simmate.workflows.relaxation import mit_workflow

nacl_structure = Structure.from_file("POSCAR")
result = mit_workflow.run(structure=nacl_structure)
```
