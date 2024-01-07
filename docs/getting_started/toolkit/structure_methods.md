# `Structure` Object Methods

----------------------------------------------------------------------

## Understanding Properties and Methods

A `Structure` object can have both `properties` and `methods`. While a property is a characteristic of an object, a method performs a specific task. For instance, the `get_primitive_structure()` method can convert a conventional unit cell into a primitive unit cell. Here's how you can use it:

```python
nacl_structure.get_primitive_structure()
```

This command will display a new structure, which should match the primitive structure we already have.

----------------------------------------------------------------------

## Storing Method Output in a New Variable

You can store the output of a method in a new `Structure` object. For instance, you can assign the output of the `get_primitive_structure()` method to a new object called `nacl_prim`:

```python
nacl_prim = nacl_structure.get_primitive_structure()
nacl_prim.density
```

----------------------------------------------------------------------

## Modifying Methods with Parameters

All methods end with parentheses `()`, which allow you to modify the method. For example, the `get_primitive_structure()` method uses symmetry in its calculations. You can adjust the tolerance for symmetry with:

```python
nacl_structure.get_primitive_structure(tolerance=0.1)
```

This command will identify atoms as symmetrical if they are nearly in their 'symmetrically correct' positions (within 0.1 Angstrom). If you don't specify a tolerance, the method will use a default value. Some methods, like `make_supercell`, require you to specify parameters, such as the supercell size. 

Here are some other methods you can use with structures:

```python
nacl_structure.add_oxidation_state_by_guess()
nacl_structure.make_supercell([2,2,2])
```

----------------------------------------------------------------------

## Discovering Other Methods and Properties

To see all the available properties and methods, type `nacl_structure.` into the terminal and press `tab`. A list of options will appear. 

You can also explore the properties and methods of other classes, such as `lattice`, using the same method. The list should look something like this (note that this image is not for a structure object):

<!-- This is an image of the Spyder's code-completion -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/console-completion.png"  height=330 style="max-height: 330px;">
</p>

While `Structure` is the most commonly used class in Simmate, there are many others. To fully understand all the options for these classes, refer to the code's documentation, which we will discuss in the next guide.

----------------------------------------------------------------------