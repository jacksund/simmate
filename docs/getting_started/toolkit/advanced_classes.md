# Advanced Classes

----------------------------------------------------------------------

## Exploring Beyond the Structure Class

This section provides a glimpse into some advanced classes and functionalities. Please note that Simmate is still in its early development stages, and there are many more features available through the [PyMatGen](https://pymatgen.org/) and [MatMiner](https://hackingmaterials.lbl.gov/matminer/) packages, which were installed alongside Simmate.

!!! tip
    If you're attempting to follow a paper and analyze a structure, chances are there's a class/function already created for that analysis! Make sure to explore the full guides or simply [post a question](https://github.com/jacksund/simmate/discussions/categories/q-a) and we'll direct you to the right path.

----------------------------------------------------------------------

## Example 1: Creating Structures

Currently, Simmate's toolkit is most effective for structure creation. This includes generating structures from random symmetry, prototype structures, and more. All we need to do is provide these "creator" classes with a composition object:

```python
from simmate.toolkit import Composition
from simmate.toolkit.creators import RandomSymStructure

composition = Composition("Ca2N")
creator = RandomSymStructure(composition)

structure1 = creator.create_structure(spacegroup=166)
structure2 = creator.create_structure(spacegroup=225)
```

----------------------------------------------------------------------

## Example 2: Fingerprint Analysis

Matminer is especially useful for analyzing a structure's features and creating machine-learning inputs. A common analysis provides the structure's fingerprint, which aids in characterizing bonding in the crystal. The most basic fingerprint is the radial distribution function (rdf) -- it displays the distance between all atoms. We can take any structure object and feed it to a matminer `Featurizer` object:

```python
from matminer.featurizers.structure.rdf import RadialDistributionFunction

rdf_analyzer = RadialDistributionFunction(bin_size=0.1)

rdf1 = rdf_analyzer.featurize(structure1)
rdf2 = rdf_analyzer.featurize(structure2)
```

We can also plot an RDF using python. Since Matminer doesn't currently offer a convenient way to plot this (with Simmate, there would be a `show_plot()` method), we can use this opportunity to learn how to plot things ourselves:

```python
import matplotlib.pyplot as plt

# The x-axis ranges from 0.1 to 20 in steps of 0.1 (in Angstroms).
# Matminer doesn't provide a list of these values but
# we can generate it using this line.
rdf_x = [n/10 + 0.1 for n in range(0, 200)]

# Create a simple line plot with lists of (x,y) values
plt.plot(rdf_x, rdf1)

# Display the plot without any additional formatting or labels.
plt.show()
```

----------------------------------------------------------------------

## Example 3: R-group Decomposition

If you have a set of molecules with a common core structure (a scaffold), you might want to identify the different R-groups attached to that core. This is a powerful tool for analyzing drug-like molecules.

```python
from simmate.toolkit import Molecule

# Load a molecule and define a scaffold (the part you want to keep)
molecule = Molecule.from_smiles("OC1=CC=C(O)C=C1")  # Hydroquinone
scaffold = Molecule.from_smiles("C1=CC=CC=C1")     # Benzene

# Identify the groups attached to the benzene ring
r_groups = molecule.get_r_groups(scaffold)

# Explore the results
print(r_groups)
```

----------------------------------------------------------------------

## Example 4: Matching Structures & Molecules

Comparing two objects to determine if they are equivalent is a common task. Simmate provides simple, unified ways to do this:

=== "Crystals"
    Using `StructureMatcher` from PyMatGen:
    ```python
    from pymatgen.analysis.structure_matcher import StructureMatcher

    matcher = StructureMatcher()
    is_matching = matcher.fit(structure1, structure2)  
    ```

=== "Molecules"
    Using Simmate's built-in comparison (based on InChI keys):
    ```python
    mol1 = Molecule.from_smiles("C")
    mol2 = Molecule.from_smiles("C")
    is_matching = (mol1 == mol2)
    ```

----------------------------------------------------------------------