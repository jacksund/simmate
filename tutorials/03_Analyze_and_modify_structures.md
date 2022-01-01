# Analyze and modify structures

In this tutorial, you will learn about coding in python and the most important class in Simmate: the `Structure` class.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [An introduction to Spyder](#an-introduction-to-spyder)
    - [The `Structure` class](#the-structure-class)
    - [Structure properties](#structure-properties)
    - [Structure methods](#structure-methods)
    - [Advanced classes](#advanced-classes)
    - [Extra Resources](#extra-resources)

> :warning: simmate still uses [pymatgen](https://pymatgen.org/) under the hood, so this tutorial is really one for using pymatgen. [Their guides](https://pymatgen.org/usage.html) also are useful, but they are written for those already familiar with python.

<br/><br/> <!-- add empty line -->

# The quick tutorial

1. In Spyder's python console, run `import simmate` to make sure everything is set up.
2. Make sure you still have our `POSCAR` file of NaCl from the last tutorial. 
3. Now let's explore the toolkit and a few of its features!

Load the structure into python and then write it to another file format:
```python
from simmate.toolkit import Structure
structure = Structure.from_file("POSCAR")
structure.to("cif", "NaCl.cif")
```

The `Structure` class (aka a `ToolkitStructure`) provides many extra properties and methods, so nearly all functions in Simmate use it as an input. This includes running workflows like we did in the previous tutorial. All available workflows can be loaded from the `simmate.workflows.all` module:
```python
from simmate.workflows.all import relaxation_mit
result = relaxation_mit.run(structure=structure)
```

Grab varius properties of the structure, lattice, and composition:
```python
# explore structure-based properties
structure.density
structure.distance_matrix
structure.cart_coords
structure.num_sites

# grab the structure's composition and access it's properties
composition = structure.composition
composition.reduced_formula
composition.elements

# grab the structure's lattice and access it's properties
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.beta
```

Make new structures using some tranformation or analysis:
```python
structure.add_oxidation_state_by_guess()
structure.make_supercell([2,2,2])
new_structure = structure.get_primitive_structure()
```

What about advanced features? Simmate is slowly adding these to our toolkit module, but many more are available through [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) (which are preinstalled for you).
```python
# Simmate is in the process of adding new features. One example
# creating a random structure from a spacegroup and composition
from simmate.toolkit import Composition
from simmate.toolkit.creators.structure.all import RandomSymStructure
composition = Composition("Ca2N")
creator = RandomSymStructure(composition)
structure = creator.create_structure(spacegroup=166)

# Matminer is handy for analyzing structures and making
# machine-learning inputs. One common analysis is the generating
# a RDF fingerprint to help analyze bonding and compare structures
from matminer.featurizers.structure.rdf import RadialDistributionFunction
rdf_analyzer = RadialDistributionFunction()
rdf = rdf_analyzer.featurize(structure)

# Pymatgen currently has the most functionality. One common
# function is checking if two structures are symmetrically
# equivalent (under some tolerance).
from pymatgen.analysis.structure_matcher import StructureMatcher
matcher = StructureMatcher()
is_matching = matcher.fit(structure1, structure2)
```

There are many more features available! If you can't find what you're looking for, be sure to ask for help before trying to code something on your own. Chances are that the feature exists somewhere -- and if we don't have it, we'll direct you to a package that does.

<br/><br/> <!-- add empty line -->

# The full tutorial

<br/> <!-- add empty line -->

## An introduction to Spyder

Prebuilt workflows can only take you so far when carrying out materials research. At some point, you'll want to make new crystal structures, modify them in some way, and perform a novel analysis on it. To do all of this, we turn away from the command-line and now start using python. If you are a brand new to coding and python, we will introduce the bare-minimum of python needed to start using simmate's toolkit in this tutorial, but we highly recommend spending 2-3 days on learning all the python fundamentals. [Codecademy's python lessons](https://www.codecademy.com/learn/learn-python-3) are a great way to learn without installing anything extra.

Ready or not, let's learn how to use Simmate's python code. Recall from tutorial 1: Anaconda gave us a bunch of programs on their home screen, such as Orange3, Jupyter Notebook, Spyder, and others. These programs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, and LibreOffice for writing papers, all of these programs are different ways to write Python. Our team uses Spyder, so we highly recommend users pick Spyder too.

If you followed tutorial 1 exactly, you should have Spyder installed and ready to go. To open it, search for Spyder in your computer's apps (use the searchbar on the bottom-left of your screen on windows 10) and select `Spyder (my_env)`. Your Spyder will be empty when you first open it up, but here's a showcase of Spyder in full swing:

<!-- This is an image of the Spyder IDE -->
<p align="center" style="margin-bottom:40px;">
<img src="https://raw.githubusercontent.com/spyder-ide/spyder/5.x/img_src/screenshot.png"  height=440 style="max-height: 440px;">
</p>

If you are comfortable with python or took the Codecademy intro course, you can get up to speed with Spyder with their intro videos. [There are 3 videos, and each is under 4 minutes](https://docs.spyder-ide.org/current/videos/first-steps-with-spyder.html).

For this tutorial, we will only be using the Python terminal (bottom-right of the screen).

<br/> <!-- add empty line -->

## The `Structure` class

In python, you'll always want to think of things as types and classify them. Individual things (or "objects") are grouped into "classes". For example, we can say that McDonalds, Burger King, and Wendy's are all **objects** of the **class** `Restaurants`.

In materials science, the class we use the most is for crystal structures, which we just call `Structure`. A crystal structure is _**always**_ made up of a lattice and a list of atomic sites. If we have those things, we have a `Structure`. This is exactly what we have in our `POSCAR` file from tutorial 2, so let's tell python that we have a `Structure`.

Start by entering `from simmate.toolkit import Structure` into the python console (bottom-right of Spyder) and hit enter. Here, we are saying we want the `Structure` class from Simmate's code. It loaded this and is now waiting for you to do something with that class.

Next, make sure you have the correct working directory (just like we did with the command-line). Spyder lists this in the top right -- and you can hit the folder icon to change it. We want it to be the same folder as where our POSCAR file is.

Next, run the line `nacl_structure = Structure.from_file("POSCAR")` in your python terminal. Here, we told python that we have a `Structure` and the information for it is located in the `POSCAR` file. This could be many other formats too -- such as a CIF file. But we now have a Structure object and it's saved as the variable named `nacl_structure`. Alternatively, we could have made this structure by hand here, instead of making a file like we did in tutorial 2:

```python
# note we can name the object whatever we want. I chose s here.
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

Either way, we now have our structure loaded and Simmate knows exactly what it is.

<br/> <!-- add empty line -->

## Structure properties

The reason we make classes and objects in python is because, once we have them, we can automate a ton of common functions and calculations. For example, all structures have a `density`, which is easily calculated once you know the lattice and atomic sites. These are known as properties. You can access this and other properties through our structure object. Try typing `nacl_structure.density` in the python terminal and hit enter. It should tell you the density!

Now what about properties for the lattice? Like volume, angles, and vectors? For all of these things, it would make sense to have a `Lattice` class that calculates all of these things for us. So that's exactly what we do -- we attach a `Lattice` object to our `Structure` object. You access it through `structure.lattice`. Try out these in your python terminal (only run one line at a time!):

```
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.beta
```

And we can apply the same idea to the list of elements in our `Structure` (known as a `Composition`):
```
composition = structure.composition
composition.reduced_formula
composition.elements
```

<br/> <!-- add empty line -->

## Structure methods

Not all aspects of a class are just fixed values. So in addition to `properties`, we also have `methods`. Methods modify our object, perform some analysis, grab other information for us. For our structure, a common method is converting to the smallest possible unitcell with symmetry. You can do this with `structure.get_primitive_structure()`. Try this in your terminal. You'll see it prints out a new structure. We can also save it to a new variable and access its properties (note, values here will be the same as our original structure because we already had the primitive unit cell):

```python
new_structure = nacl_structure.get_primitive_structure()
new_structure.density
```

Note we need paratheses `()` at the end of the method. This is because methods act like functions -- that is they can often accept options to change their analysis and output. For example, we could have changed our symmetry tolerance by doing:

```python
nacl_structure.get_primitive_structure(tolerance=0.1)
```

There are many other methods available for structures too:
```python
structure.add_oxidation_state_by_guess()
structure.make_supercell([2,2,2])
```

To get a quick look at **all** of the properties and methods available, type `nacl_structure` into the terminal but don't hit enter yet. Then add a period so you have `nacl_structure.`, and finally, hit tab. You should see a list pop up with everything available. Try selecting lattice, and then do this tab trick again! The list should look similar to this (this image isn't for a structure object though):

<!-- This is an image of the Spyder's code-completion -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/console-completion.png"  height=330 style="max-height: 330px;">
</p>

This can be done with any class and object! There are many different classes in Simmate, but you'll interact with `Structure` the most. To fully understand all of the options for these classes, you'll need to explore the code's documentation, which we will cover in the next tutorial.

<br/> <!-- add empty line -->

## Advanced classes

To give you a sneak-peak of some advanced classes and functionality, we outline some examples in this section. Note that Simmate is still early in development, so there are many more features available through [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) packages, which were installed alongside Simmate.

Simmate's toolkit is (at the moment) most useful for structure creation. This includes creating structures from random symmetry, prototype structures, and more.
We only need to give these "creator" classes a composition object:
```python
from simmate.toolkit import Composition
from simmate.toolkit.creators.structure.all import RandomSymStructure
composition = Composition("Ca2N")
creator = RandomSymStructure(composition)
structure = creator.create_structure(spacegroup=166)
```

Matminer is particularly useful for analyzing "features" of a structure and making machine-learning inputs. One common analysis gives the "fingerprint" of the structure, which helps characterize bonding in the crystal. The most basic fingerprint is the radial distribution function (rdf) -- it shows the distribution of all atoms from one another. We take any structure object and can feed it a fingerprint-analyzer object:

```python
from matminer.featurizers.structure.rdf import RadialDistributionFunction
rdf_analyzer = RadialDistributionFunction()
rdf = rdf_analyzer.featurize(structure)
```

Pymatgen is currently the largest package and has the most toolkit-like features. As a small example, it's common to compare two structures and see if are symmetrically equivalent (within a given tolerance). You give it two structures and it will return True or False on whether they are matching:
```python
from pymatgen.analysis.structure_matcher import StructureMatcher
matcher = StructureMatcher()
is_matching = matcher.fit(structure1, structure2)
```

If you're trying to follow a paper and analyze a structure, odds are that someone made a class/function for that analysis! Be sure to search around the documentation for it (next tutorial teaches you how to do this) or just [post a question](https://github.com/jacksund/simmate/discussions/new?category=q-a) and we'll point you in the right direction.

<br/> <!-- add empty line -->

## Extra resources

- [Codecademy's python lessons](https://www.codecademy.com/learn/learn-python-3) (we HIGHLY recommend spending 2-3 days going through if you're new to python. Learning the fundamentals is very important to using Simmate effectively.)
- [Introduction to Spyder](https://docs.spyder-ide.org/current/videos/first-steps-with-spyder.html) (The 3 videos are under 4 minutes each, so worth a quick watcg) 

