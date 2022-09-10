
# Methods of a `Structure` object

----------------------------------------------------------------------

## Properties vs Methods

In addition to `properties`, an object can also have `methods`. Typically, a method will perform a calculation; it may also save the results of that calculation. For example, you might want to convert a conventional unit cell into a primitive unit cell.  You can do this with `nacl_structure.get_primitive_structure()`. Try this in your python console:

```python
nacl_structure.get_primitive_structure()
```

You'll see it prints out a new structure. We had the primitive structure already, so it should be identical to our output from before.

----------------------------------------------------------------------

## Save the output to a new variable

For this method, we save it as a new `Structure` object by assigning it to the name `nacl_prim`:

```python
nacl_prim = nacl_structure.get_primitive_structure()
nacl_prim.density
```

----------------------------------------------------------------------

## Giving parameters to methods

Note that all methods end with parentheses `()`. This allows us to alter the method. For example, get_primitive_structure() makes use of symmetry in its calculation, so if we do:

```python
nacl_structure.get_primitive_structure(tolerance=0.1)
```

The calculation will allow atoms that are nearly in their 'symmetrically correct' positions (within 0.1 Å) to be identiified as symmetrical. Note, we didn't have to set a tolerance before because there are default values being used. Some methods don't have defaults. For example, the `make_supercell` method require you to specify a supercell size. 

There are many other methods available for structures too:

```python
nacl_structure.add_oxidation_state_by_guess()
nacl_structure.make_supercell([2,2,2])
```

----------------------------------------------------------------------

## Exploring other methods and properties

To get a quick look at **all** of the properties and methods available, type `nacl_structure` into the terminal but don't hit enter yet. Then add a period so you have `nacl_structure.`, and finally, hit `tab`. You should see a list pop up with everything available. 

Select lattice, then do this tab trick again. The list should look similar to this (this image isn't for a structure object though):

<!-- This is an image of the Spyder's code-completion -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/console-completion.png"  height=330 style="max-height: 330px;">
</p>

This can be done with any class or any object. There are many different classes in Simmate, but you'll interact with `Structure` the most. To fully understand all of the options for these classes, you'll need to explore the code's documentation, which we will cover in the next guide.

----------------------------------------------------------------------
