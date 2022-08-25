
# Advanced classes

## Beyond the Structure class

To give you a sneak-peak of some advanced classes and functionality, we outline some examples in this section. Note that Simmate is still early in development, so there are many more features available through [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) packages, which were installed alongside Simmate.

## Example 1: Structure Creation

Simmate's toolkit is (at the moment) most useful for structure creation. This includes creating structures from random symmetry, prototype structures, and more.
We only need to give these "creator" classes a composition object:

```python
from simmate.toolkit import Composition
from simmate.toolkit.creators import RandomSymStructure

composition = Composition("Ca2N")
creator = RandomSymStructure(composition)

structure1 = creator.create_structure(spacegroup=166)
structure2 = creator.create_structure(spacegroup=225)
```

## Example 2: Fingerprint analysis

Matminer is particularly useful for analyzing "features" of a structure and making machine-learning inputs. One common analysis gives the "fingerprint" of the structure, which helps characterize bonding in the crystal. The most basic fingerprint is the radial distribution function (rdf) -- it shows the distance of all atoms from one another. We take any structure object and can feed it to a matminer `Featurizer` object:

```python
from matminer.featurizers.structure.rdf import RadialDistributionFunction

rdf_analyzer = RadialDistributionFunction(bin_size=0.1)

rdf1 = rdf_analyzer.featurize(structure1)
rdf2 = rdf_analyzer.featurize(structure2)
```

We can plot an RDF using python too. Matminer doesn't have a convenient way to plot this for us yet (with Simmate there would be a `show_plot()` method), so we can use this opportunity to learn how to plot things ourselves:

```python
import matplotlib.pyplot as plt

# The x-axis goes from 0.1 to 20 in steps 0.1 (in Angstroms).
# Matminer doesn't give us a list of these values but
# we can make it using this line.
rdf_x = [n/10 + 0.1 for n in range(0, 200)]

# Make a simple line plot with lists of (x,y) values
plt.plot(rdf_x, rdf1)

# Show the plot without any fancy formatting or labels.
plt.show()
```

## Example 3: Structure matching

Pymatgen is currently the largest package and has the most toolkit-like features. As an example, it's common to compare two structures and see if are symmetrically equivalent (within a given tolerance). You give it two structures and it will return True or False on whether they are matching:

```python
from pymatgen.analysis.structure_matcher import StructureMatcher

matcher = StructureMatcher()

# Now compare our two random structures!
# This should give False. Check in your Spyder variable explorer.
is_matching = matcher.fit(structure1, structure2)  
```

!!! tip
    If you're trying to follow a paper and analyze a structure, odds are that someone made a class/function for that analysis! Be sure to search around the documentation for it (next tutorial teaches you how to do this) or just [post a question](https://github.com/jacksund/simmate/discussions/categories/q-a) and we'll point you in the right direction.

