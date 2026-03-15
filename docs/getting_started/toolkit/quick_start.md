# Analyzing & Modifying Structures

!!! tip
    Simmate's toolkit is built on top of [PyMatGen](https://pymatgen.org/) (for crystals) and [RDKit](https://www.rdkit.org/) (for molecules). This tutorial serves as a guide to using these packages through a simplified, unified interface.

## Quick Start

### 1. Crystals (Structures)

Load a structure from a file (like the `POSCAR` from the previous tutorial) and access its properties:

```python
from simmate.toolkit import Structure

# Load from a file
structure = Structure.from_file("POSCAR")

# Access properties
print(f"Density: {structure.density}")
print(f"Volume: {structure.lattice.volume}")
print(f"Formula: {structure.composition.reduced_formula}")

# Modify and export
structure.make_supercell([2,2,2])
structure.to(filename="NaCl_supercell.cif", fmt="cif")
```

### 2. Molecules

Load a molecule from a SMILES string and explore its features:

```python
from simmate.toolkit import Molecule

# Load from a SMILES string (e.g., Caffeine)
molecule = Molecule.from_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")

# Access properties
print(f"Molecular Weight: {molecule.molecular_weight}")
print(f"Number of Rings: {molecule.num_rings}")
print(f"LogP: {molecule.log_p_rdkit}")

# Export to a file
molecule.to_sdf_file("caffeine.sdf")
```

## Extra Examples

Looking for advanced features? Simmate incorporates many analytical tools directly into our toolkit, but even more are available through the underlying packages.

### Random Structure Creation

Creating a random structure from a spacegroup and composition:

```python
from simmate.toolkit import Composition
from simmate.toolkit.creators import RandomSymStructure

composition = Composition("Ca2N")
creator = RandomSymStructure(composition)

structure = creator.create_structure(spacegroup=166)
```

### Fingerprints

Fingerprints are useful for comparing structures or molecules and creating machine-learning inputs.

=== "Crystals"
    ```python
    # Using MatMiner (preinstalled with simmate)
    from matminer.featurizers.structure.rdf import RadialDistributionFunction
    
    rdf_analyzer = RadialDistributionFunction(bin_size=0.1)
    rdf = rdf_analyzer.featurize(structure)
    ```

=== "Molecules"
    ```python
    # Built-in to Simmate's Molecule class
    fingerprint = molecule.fingerprint
    ```

### Structure/Molecule Matching

Check if two objects are equivalent:

=== "Crystals"
    ```python
    from pymatgen.analysis.structure_matcher import StructureMatcher
    
    matcher = StructureMatcher()
    is_matching = matcher.fit(structure1, structure2)
    ```

=== "Molecules"
    ```python
    # Molecules can be compared directly
    is_matching = (molecule1 == molecule2)
    ```
