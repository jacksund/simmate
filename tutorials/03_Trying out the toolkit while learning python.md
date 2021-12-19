# Trying out the toolkit while learning python

> :warning: simmate still uses [pymatgen](https://pymatgen.org/) under the hood, so this tutorial is really one for using pymatgen. Pymatgen is central to using Simmate, so we still include this in our tutorial series!

## The quick version

1. In Spyder's python console, run `import simmate` to make sure everything is set up.
2. Make sure you still have our `POSCAR` file of NaCl from the last tutorial. 
3. Now let's explore the toolkit and a few of its features!

Load the structure into python and then write it to a CIF file
```python
from simmate.shortcuts import Structure
structure = Structure.from_file("POSCAR")
structure.to("cif", "NaCl.cif")
```

Grab varius properties of the structure
```python
# explore structure-based properties
structure.density
structure.distance_matrix
structure.coordinates_cartesian
structure.nsites

# grab the structure's composition and access it's properties
compositon = structure.composition
composition.formula_reduced
composition.elements

# grab the structure's lattice and access it's properties
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.angle_beta
```

Make new structures using some tranformation or analysis
```python
# all get_* methods leave the original structure unchanged and return a new structure
new_structure_01 = structure.get_supercell([2,2,2])
new_structure_02 = structure.get_conventional_unitcell()
new_structure_03 = structure.get_primitive_unitcell()
new_structure_04 = structure.get_oxidation_states()
```

What about advanced features?
```python
# Generate a RDF fingerprint to help analyze and compare structures
from simmate.toolkit.fingerprints.all import RdfFingerprint
fingerprint_analyzer = RdfFingerprint()
rdf = fingerprint_analyzer.get_fingerprint(structure)

# Create a random structure from a spacegroup and composition
from simmate.toolkit.creators.all import PyXtalCreator
creator = PyXtalCreator(composition)
structure = creator.new_structure(spacegroup=166)

# Check if two structures are matching
from simmate.toolkit.matching import StructureMatcher
matcher = StructureMatcher
is_matching = matcher.match(structure1, structure2)
```
There are many more features available! If you can't find what you're looking for, be sure to ask for help before trying to code something on your own. Chances are that the feature exists somewhere -- and if we don't have it, we'll direct you to a package that does.

## The full tutorial

### An introduction to Spyder

Prebuilt workflows can only take you so far when carrying out materials research. At some point, you'll want to make new crystal structures, modify them in some way, and perform a novel analysis on it. To do all of this, we turn away from the command-line and now start using python. If you are a brand new to coding and python, we will introduce the bare-minimum of python needed to start using simmate's toolkit in this tutorial, but we highly recommend spending 2-3 days on learning all the python fundamentals. [Codecademy's python lessons](https://www.codecademy.com/learn/learn-python-3) are a great way to learn without installing anything.

Ready or not, let's learn how to use Simmate's python code. [Recall from tutorial 1](https://github.com/jacksund/simmate/blob/main/tutorials/01_Installing%20Simmate%20while%20learning%20the%20command-line.md#installing-anaconda-and-a-first-look): Anaconda gave us a bunch of programs on their home screen, such as Orange3, Jupyter Notebook, Spyder, and others. These programs are for you to write your own python code. Just like how there is Microsoft Word, Google Docs, and LibreOffice for writing papers, all of these programs are different ways to write Python. Our team uses Spyder, so we highly recommend users pick Spyder too.

If you followed tutorial 1 exactly, you should have Spyder installed and ready to go. Open Spyder and make sure it's the Spyder linked to your custom python environment. For example, when you search for Spyder in your apps on Windows 10, you'd select `Spyder (my_env)`. Your Spyder will be empty when you first open it up, but here's a showcase of Spyder in full swing:

<!-- This is an image of the Spyder IDE -->
<p align="center" style="margin-bottom:40px;">
<img src="https://raw.githubusercontent.com/spyder-ide/spyder/5.x/img_src/screenshot.png"  height=440 style="max-height: 440px;">
</p>

If you are comfortable with python or took the Codecademy intro course, you can get up to speed with Spyder with their intro videos. [There are 3 videos, and each is under 4 minutes](https://docs.spyder-ide.org/current/videos/first-steps-with-spyder.html).

For this tutorial, we will only be using the Python terminal (bottom-right of the screen).

### The `Structure` class

In python, you'll always want to think of things as types and classify them. Individual things (or "objects") are grouped into "classes". For example, we can say that McDonalds, Burger King, and Wendy's are all **objects** of the **class** `Restaurants`. 

In materials science, the class we use the most is for crystal structures, which we just call `Structure`. A crystal structure is _**always**_ made up of a lattice and a list of atomic sites. If we have those things, we have a `Structure`. This is exactly what we have in our `POSCAR` file from tutorial 2, so let's tell python that we have a `Structure`.

Start by entering `from simmate.shortcuts import Structure` into the python console (bottom-right of Spyder) and hit enter. Here, we are saying we want the `Structure` class from Simmate's code. It loaded this and is now waiting for you to do something with that class.

Next, make sure you have the correct working directory (just like we did with the command-line). Spyder lists this in the top right -- and you can hit the folder icon to change it. We want it to be the same folder as where our POSCAR file is.

Next, run the line `nacl_structure = Structure.from_file("POSCAR")` in your python terminal. Here, we told python that we have a `Structure` and the information for it is located in the `POSCAR` file. This could be many other formats too -- such as a CIF file. But We now have a Structure object and it's saved as the variable named `nacl_structure`. Alternatively, we could have made this structure by hand here, instead of making a file like we did in tutorial 2:

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

Either way, we now have our structure loaded and Simmate now knows exactly what it is.

### Structure properties

The reason we make classes and objects in python is because, once we have them, we can automate a ton of common functions and calculations. For example, all structures have a `density`, which is easily calculated once you know the lattice and atomic sites. These are known as properties. You can access this and other properties through our structure object. Try typing `nacl_structure.density` in the python terminal and hit enter. It should tell you the density!

Now what about properties for the lattice? Like volume, angles, and vectors? For all of these things, it would make sense to have a `Lattice` class that calculates all of these things for us. So that's exactly what we do -- we attach a `Lattice` object to our `Structure` object. You access it through `structure.lattice`. Try out these in your python terminal:

```
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.angle_beta
```

And we can apply the same idea to the list of elements in our `Structure` (known as a `Composition`):
```
compositon = structure.composition
composition.formula_reduced
composition.elements
```

### Structure methods

Not all aspects of a class are just fixed values. So in addition to `properties`, we also have `methods`. Methods modify our object, perform some analysis, grab other information for us. For our structure, a common method is converting the the smallest possible unitcell with symmetry. You can do this with `structure.get_primitive_structure()`. Try this in your terminal. You'll see it prints out a new structure. We can also save it to a new variable and access its properties (which will be the same because we already had the primitive unit cell):

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
new_structure_01 = nacl_structure.make_supercell([2,2,2])
new_structure_02 = nacl_structure.get_space_group_info()
```

To get a quick look at **all** of the properties and methods available, type `nacl_structure` into the terminal but don't hit enter yet. Then add a period so you have `nacl_structure.`, and finally, hit tab. You should see a list pop up with everything available. Try selecting lattice, and then do this tab trick again! The list should look like this (this image isn't for a structure object though):

<!-- This is an image of the Spyder's code-completion -->
<p align="center" style="margin-bottom:40px;">
<img src="https://docs.spyder-ide.org/current/_images/console-completion.png"  height=330 style="max-height: 330px;">
</p>

This can be done with any class and object! There are many different classes in Simmate, but you'll interact with `Structure` the most. To fully understand all of the options for these classes, you'll need to explore the code's documentation, which we will cover in the next tutorial.

### Advanced classes

To give you a sneak-peak of some advanced classes and functionality, here are some example. 

First, there are advanced analyses you can use. One is known as a "fingerprint" of the structure, which helps represent and understand bonding in the crystal. The most basic fingerprint is the radial distribution function (rdf). It shows the distribution of all atoms from one another. We take any structure object and can feed it a fingerprint-analyzer object:

```python
from simmate.toolkit.fingerprints.all import RdfFingerprint
fingerprint_analyzer = RdfFingerprint()
rdf = fingerprint_analyzer.get_fingerprint(structure)
```

We also can randomly create structures with a structure-creator class. We only need to give it a composition object:
```python
from simmate.toolkit.creators.all import PyXtalCreator
creator = PyXtalCreator(composition)
structure = creator.new_structure(spacegroup=166)
```

Lastly, it's common to compare two structures and seeing if are symmetrically the same structure. There's a StructureMatcher class for that:
```python
from simmate.toolkit.matching import StructureMatcher
matcher = StructureMatcher
is_matching = matcher.match(structure1, structure2)
```

If you're trying something new, odds are that someone made a class/function for it! Be sure to search around our documentation for it (next tutorial teaches you how to search) or just [post a question](https://github.com/jacksund/simmate/discussions/new?category=q-a) and we'll point you in the right direction.
