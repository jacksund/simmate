# Analyzing & Modifying Structures

## Quick Start

!!! tip
    Simmate is built on [pymatgen](https://pymatgen.org/). Therefore, this tutorial also serves as a guide to using their package. Explore [their guides](https://pymatgen.org/usage.html) for extra help.

1. Ensure you have the `POSCAR` file of NaCl from the previous tutorial.

2. You can load the structure into python and then convert it to another file format:
```python
from simmate.toolkit import Structure

structure = Structure.from_file("POSCAR")
structure.to(filename="NaCl.cif", fmt="cif")
```

3. You can run workflows by providing a filename or `Structure` object
```python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.mit")

# option 1
workflow.run(structure="POSCAR")

# option 2
workflow.run(structure=structure)  # uses var from previous step
```

4. Access various properties of the structure, lattice, and composition:
```python
# explore structure-based properties
structure.density
structure.distance_matrix
structure.cart_coords
structure.num_sites

# access the structure's composition and its properties
composition = structure.composition
composition.reduced_formula
composition.elements

# access the structure's lattice and its properties
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.beta
```

5. Create new structures using some transformation or analysis:
```python
structure.add_oxidation_state_by_guess()
structure.make_supercell([2,2,2])
new_structure = structure.get_primitive_structure()
```

## Extra 

Looking for advanced features? Simmate is gradually incorporating these into our toolkit module, but many more are available through [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) (which are preinstalled for you).

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

# Matminer is useful for analyzing structures and creating
# machine-learning inputs. One common analysis is the generating
# a RDF fingerprint to help analyze bonding and compare structures

from matminer.featurizers.structure.rdf import RadialDistributionFunction

rdf_analyzer = RadialDistributionFunction(bin_size=0.1)

rdf1 = rdf_analyzer.featurize(structure1)
rdf2 = rdf_analyzer.featurize(structure2)

# ----------------------------------------------------------------------

# Pymatgen currently offers the most functionality. One common
# function is checking if two structures are symmetrically
# equivalent (under some tolerance).

from pymatgen.analysis.structure_matcher import StructureMatcher

matcher = StructureMatcher()

# Now compare our two random structures!
# This should give False. Check in your Spyder variable explorer.
is_matching = matcher.fit(structure1, structure2)
```

There are many more features available! If you can't find what you're looking for, don't hesitate to ask for help before trying to code something on your own. The feature you're looking for probably exists somewhere -- and if we don't have it, we'll guide you to a package that does.
