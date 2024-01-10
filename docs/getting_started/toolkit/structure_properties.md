# Understanding the `Structure` Object Properties

----------------------------------------------------------------------

## The Role of Classes in Defining Properties

Classes are created to automate routine calculations. 

For instance, all structures possess a `density` property, which can be computed once the lattice and atomic sites are known. The formula for this calculation remains constant, allowing for automation. 

Access this and other properties through the structure object. For example, input `nacl_structure.density` in the python terminal and press enter to display the density of the structure:

``` python
nacl_structure.density
```

----------------------------------------------------------------------

## Exploring Lattice Properties

What about other lattice properties such as volume, angles, and vectors? 

For better organization, the `Structure` class includes an associated class called `Lattice`. Within the `lattice` object, properties like `volume` can be found. Test these in your python terminal (run one line at a time):

```python
nacl_structure.lattice.volume
nacl_structure.lattice.matrix
nacl_structure.lattice.beta
```

The expected outputs are...

```
# EXPECTED OUTPUTS

46.09614820053437

array([[3.48543651, 0.        , 2.01231771],
       [1.16181217, 3.28610106, 2.01231771],
       [0.        , 0.        , 4.02463542]])

59.99999999999999
```

For convenience, you can use a shortcut. Save the `Lattice` object to a new variable name (here, it's `nacl_lat`, but you can choose a different name) and then call its properties:

```python
nacl_lat = nacl_structure.lattice
nacl_lat.volume
nacl_lat.matrix
nacl_lat.beta
```

The outputs will be identical to the previous ones.

----------------------------------------------------------------------

## Investigating Composition Properties

The same concept can be applied to other `Structure` sub-classes, such as `Composition`. This enables us to view properties related to composition:
```
nacl_compo = nacl_structure.composition
nacl_compo.reduced_formula
nacl_compo.elements
```

The expected outputs are...

```
# EXPECTED OUTPUTS

Comp: Na1 Cl1

'NaCl'

[Element Na, Element Cl]  # <-- these are Element objects!
```

----------------------------------------------------------------------

## Managing Variables

As you create new python objects and assign them different names, you'll need a way to keep track of them. Spyder's variable explorer (located in the top right window tab) can help with this! Try double-clicking on some of your variables to explore what Spyder can do:

<!-- This is an image of the Spyder IDE variable explorer -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/variable-explorer-execution.gif"  height=440 style="max-height: 440px;">
</p>

----------------------------------------------------------------------