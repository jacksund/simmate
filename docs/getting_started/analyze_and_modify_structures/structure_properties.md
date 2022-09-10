
# Properties of a `Structure` object

----------------------------------------------------------------------

## Classes give us properties

We make classes because they allow us to automate common calculations. 

For example, all structures have a `density`, which is easily calculated once you know the lattice and atomic sites. The formula to calculate is always the same, so we can automate the calculation. 

You can access this and other properties through our structure object. Try typing `nacl_structure.density` in the python terminal and hit enter. It should tell you the density of our structure:

``` python
nacl_structure.density
```

----------------------------------------------------------------------

## Lattice properties

Now what about other properties for the lattice, like volume, angles, and vectors? 

For the sake of organization, the `Structure` class has an associated class called `Lattice`, and within the `lattice` object we find properties like `volume`. Try out these in your python terminal (only run one line at a time):

```python
nacl_structure.lattice.volume
nacl_structure.lattice.matrix
nacl_structure.lattice.beta
```

Your outputs will be...

```
# EXPECTED OUTPUTS

46.09614820053437

array([[3.48543651, 0.        , 2.01231771],
       [1.16181217, 3.28610106, 2.01231771],
       [0.        , 0.        , 4.02463542]])

59.99999999999999
```

If you don't like to type long lines, there is a shortcut.  We save the `Lattice` object (here, we call it as `nacl_lat`, but you can pick a different name) to a new variable name and then call its properties:

```python
nacl_lat = nacl_structure.lattice
nacl_lat.volume
nacl_lat.matrix
nacl_lat.beta
```

Note, outputs will be the same as above.

----------------------------------------------------------------------

## Composition properties

We can apply the same idea to other `Structure` sub-classes, such as `Composition`. This allows us to see properties related to composition:
```
nacl_compo = nacl_structure.composition
nacl_compo.reduced_formula
nacl_compo.elements
```

This will give outputs of...

```
# EXPECTED OUTPUTS

Comp: Na1 Cl1

'NaCl'

[Element Na, Element Cl]  # <-- these are Element objects!
```

----------------------------------------------------------------------

## Keeping track of our variables

As you create new python objects and name them different things, you'll need help keep track of them. Fortunately, Spyder's variable explorer (a tab in top right window) let's us track them! Try double-clicking some of your variables and explore what Spyder can do:

<!-- This is an image of the Spyder IDE variable explorer -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/variable-explorer-execution.gif"  height=440 style="max-height: 440px;">
</p>

----------------------------------------------------------------------
