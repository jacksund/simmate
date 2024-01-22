# Analyzing & Modifying Structures

!!! tip
    Simmate toolkit still uses [pymatgen](https://pymatgen.org/). Therefore, this tutorial also serves as a guide to using their package. See also:

    - outline of all available methods & properties (see `Full Guides` > `Toolkit`)
    - [PyMatGen's official guides & API reference](https://pymatgen.org/usage.html)

## Quick Start

1. Ensure you have the `POSCAR` file of NaCl from the previous tutorial.

2. You can load the structure into python:
```python
from simmate.toolkit import Structure

structure = Structure.from_file("POSCAR")
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
```

6. Export your final structure to a new file format:
```python
structure.to(filename="NaCl.cif", fmt="cif")
```

## Extra Examples

Looking for advanced features? Simmate is gradually incorporating these into our toolkit module, but many more are available through [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) (which are preinstalled for you).

### Random Structure Creation

Creating a random structure from a spacegroup and composition:

```python
from simmate.toolkit import Composition
from simmate.toolkit.creators import RandomSymStructure

composition = Composition("Ca2N")
creator = RandomSymStructure(composition)

structure = creator.create_structure(spacegroup=166)
```

### Fingerprints (MatMiner)

Matminer is useful for analyzing structures and creating machine-learning inputs. One common analysis is the generating a RDF fingerprint to help analyze bonding and compare structures:

```python
from matminer.featurizers.structure.rdf import RadialDistributionFunction

rdf_analyzer = RadialDistributionFunction(bin_size=0.1)
rdf = rdf_analyzer.featurize(structure)
```

### Structure Matching (PyMatGen)

Pymatgen currently offers the most functionality. One common function is checking if two structures are symmetrically equivalent (under some tolerance):

```python
from pymatgen.analysis.structure_matcher import StructureMatcher

matcher = StructureMatcher()
is_matching = matcher.fit(structure1, structure2)
```
