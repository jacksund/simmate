# Analyze and modify structures

In this tutorial, you will learn about the most important class in Simmate: the `Structure` class. Beginners will also be introduced to classes and the Spyder IDE.

!!! note
    Simmate uses [pymatgen](https://pymatgen.org/) under the hood, so this tutorial is really one for using their package. [Their guides](https://pymatgen.org/usage.html) also are useful, but they are written for those already familiar with python.

----------------------------------------------------------------------

# The quick tutorial

1. In Spyder's python console, run `import simmate` to make sure everything is set up.
2. Make sure you still have our `POSCAR` file of NaCl from the last tutorial. 
3. Now let's explore the toolkit and a few of its features!

Load the structure into python and then write it to another file format:
```python
from simmate.toolkit import Structure
structure = Structure.from_file("POSCAR")
structure.to(filename="NaCl.cif", fmt="cif")
```

The `Structure` class (aka a `ToolkitStructure`) provides many extra properties and methods, so nearly all functions in Simmate use it as an input. This includes running workflows like we did in the previous tutorial. All available workflows can be loaded from the `simmate.workflows` module:
```python
from simmate.workflows.relaxation import mit_workflow
result = mit_workflow.run(structure=structure)
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
from simmate.toolkit.creators import RandomSymStructure

composition = Composition("Ca2N")
creator = RandomSymStructure(composition)

structure1 = creator.create_structure(spacegroup=166)
structure2 = creator.create_structure(spacegroup=225)

# ----------------------------------------------------------------------

# Matminer is handy for analyzing structures and making
# machine-learning inputs. One common analysis is the generating
# a RDF fingerprint to help analyze bonding and compare structures

from matminer.featurizers.structure.rdf import RadialDistributionFunction

rdf_analyzer = RadialDistributionFunction(bin_size=0.1)

rdf1 = rdf_analyzer.featurize(structure1)
rdf2 = rdf_analyzer.featurize(structure2)

# ----------------------------------------------------------------------

# Pymatgen currently has the most functionality. One common
# function is checking if two structures are symmetrically
# equivalent (under some tolerance).

from pymatgen.analysis.structure_matcher import StructureMatcher

matcher = StructureMatcher()

# Now compare our two random structures!
# This should give False. Check in your Spyder variable explorer.
is_matching = matcher.fit(structure1, structure2)
```

There are many more features available! If you can't find what you're looking for, be sure to ask for help before trying to code something on your own. Chances are that the feature exists somewhere -- and if we don't have it, we'll direct you to a package that does.

----------------------------------------------------------------------
