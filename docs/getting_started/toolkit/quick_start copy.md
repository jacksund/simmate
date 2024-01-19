# Single-Molecule Quick Start

--------------------------------------------------------------------------------

## Summary of Steps

A typical workflow for a single molecule usually involves the following steps:

1. Importing a molecule into Python
2. Cleaning up the molecule's structure
3. Analyzing the molecule's properties and features
4. Exporting the molecule in a different format

While only the first step is mandatory, the rest are optional and can be customized according to your needs. Use the guides in this section to explore the various options available for each step. You can combine these options to create a unique script or workflow that can be shared with others!

--------------------------------------------------------------------------------

## Basic Example

Here's a simple example that covers each of the steps mentioned above:

``` python
from simmate_corteva.toolkit import Molecule

# 1: Import
molecule = Molecule.from_smiles("C1=CC(=C(C=C1CCN)O)O")

# 2: Clean / Format
molecule.convert_to_3d(keep_hydrogen=True)

# 3a: Analyze Functional Groups
print("Functional groups identified:")
print(molecule.get_fragments())

# 3b: Analyze Stereochemistry
if molecule.num_stereocenters > 0:
    print("Stereocenters detected!")

# 4: Export
molecule.to_sdf_file(filename="my_3d_mol.sdf")
```

Additionally, if you're using Spyder or Jupyter Notebooks as your Python IDE, you can visualize your molecule with the following command:

``` python
molecule.image
```

--------------------------------------------------------------------------------