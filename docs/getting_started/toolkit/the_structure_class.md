# The `Structure` Class

## Understanding Classes in Python

Python "classes" and "objects" are key concepts in Python programming. 

Consider this analogy: McDonald's, Burger King, and Wendy's are examples of restaurants. In Python, we could say that `mcdonalds`, `burgerking`, and `wendys` are **objects** of the **class** `Restaurants`.  

By grouping **objects** into **classes**, Python streamlines programming. For instance, we could design the `Restaurants` class to have a property called `menu`. Then, we could view the menu simply by typing `wendys.menu`. This sets a rule that the menu info can be accessed with `example_restaurant.menu` for any restaurant.

This becomes incredibly powerful when we start building out functionality and analyses.

----------------------------------------------------------------------

## Importing the Structure Class

In materials science, the most commonly used class is for crystal structures. In Simmate, this class is called `Structure`. A crystal structure always consists of a lattice and a list of atomic sites. This is exactly what we have in our `POSCAR` file from tutorial 2, so let's use Simmate to create an object of the `Structure`.

Enter this line into the Python console:

```python
from simmate.toolkit import Structure
```

This line imports the `Structure` class from Simmate's code. The `Structure` class is now loaded into memory and ready for use.

----------------------------------------------------------------------

## Loading a Structure from a File

Next, ensure you have the correct working directory (as we did with the command-line). Spyder displays this in the top right, and you can change it by clicking the folder icon. We want to be in the same folder as our POSCAR file. Run this line in your Python terminal:

```python
nacl_structure = Structure.from_file("POSCAR")
```

Here, we're telling Python that we have a `Structure` and its information is located in the `POSCAR` file. This could be in many other formats, such as a CIF file. But now we have a `Structure` object named `nacl_structure`. To verify it loaded correctly, run this line:

```python
nacl_structure
```

It should print out the same information from our POSCAR. 

----------------------------------------------------------------------

## Creating a Structure Manually in Python

Alternatively, we could have created this structure manually:

```python
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

----------------------------------------------------------------------

## Using the Structure in a Workflow

Regardless of how you created a structure, we now have our `Structure` object and we can use its properties (and methods) to simplify our calculations.

For instance, we can use it to run a workflow. We did this with the command-line in the last tutorial but can accomplish the same thing with Python:

=== "python"
    ```python
    from simmate.toolkit import Structure
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("static-energy.vasp.mit")
    
    nacl_structure = Structure.from_file("POSCAR")
    
    result = workflow.run(structure=nacl_structure)
    ```

If we don't need to modify the structure, we could have just given the filename to our workflow:

=== "python"
    ```python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("static-energy.vasp.mit")
    result = workflow.run(structure="POSCAR")
    ```

=== "yaml"
    ``` yaml
    workflow_name: static-energy.vasp.mit
    structure: POSCAR
    ```

----------------------------------------------------------------------