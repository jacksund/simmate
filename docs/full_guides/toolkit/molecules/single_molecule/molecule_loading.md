# Loading a Molecule

--------------------------------------------------------------------------------

## Introduction

To load a molecule, call a `from_` method of `Molecule`. 

For instance, `from_smiles` for a SMILES input, `from_mol2` for a MOL2 input, and `from_rdkit` for an RDKit object. Choose the method that corresponds to your input type, or use the `from_dynamic` strategy if you're unsure or have a variety of input types.

!!! tip
    `from_dynamic` is the simplest and most convenient method, but it may not always work! If you know your molecule's format, use the specific method for it.

--------------------------------------------------------------------------------

## Dynamic Loading

Dynamic loading examines your input and determines how to convert it into a `Molecule` object. It performs checks and then calls one of the methods detailed on this page.

``` python
from simmate.toolkit import Molecule

# try this with a filename, a smiles string, SDF string, rdkit object, ...
input_01 = "example_molecule.sdf"
input_02 = "example_molecule.csv" 
input_03 = "C1=CC(=C(C=C1CCN)O)O"

# The from_dynamic method will determine the format and convert it
for new_input in [input_01, input_02, input_03]
    molecule = Molecule.from_dynamic(new_input)
```

!!! note
    `from_dynamic` also checks if we already have a `Molecule` object and returns it if we do.

--------------------------------------------------------------------------------

## Basic Loading

### Files

File-based inputs accept a filename as a string or a `pathlib.Path` object.

``` python
from simmate.toolkit import Molecule

molecule = Molecule.from_sdf_file("example.sdf")
```

| TYPE              | METHOD             |
| ----------------- | ------------------ |
| (dynamic loading) | `from_file`        |
| CSV               | `from_csv_file`    |
| SMILES (any type) | `from_smiles_file` |
| SDF (aka CTAB)    | `from_sdf_file`    |
| MOL2              | `from_mol2_file`   |

!!! tip
    Each of these methods has a corresponding submethod for loading this format directly from text/str, detailed in the section below. For instance, `from_smiles` takes a string, while `from_smiles_file` takes a `.smi` file.

--------------------------------------------------------------------------------

### Raw text / strings

You can read a python string variable directly. These methods are primarily used for testing and debugging.

``` python
from simmate.toolkit import Molecule

molecule = Molecule.from_smiles("C1=CC(=C(C=C1CCN)O)O")
```

| TYPE           | METHOD        |
| -------------- | ------------- |
| INCHI          | `from_inchi`  |
| SMILES         | `from_smiles` |
| SMARTS         | `from_smarts` |
| SDF (aka CTAB) | `from_sdf`    |
| MOL2           | `from_mol2`   |

!!! tip
    Each of these methods has a corresponding submethod for loading this format directly from a file, detailed in the section above. For instance, `from_smiles` takes a string, while `from_smiles_file` takes a `.smi` file.

--------------------------------------------------------------------------------

### Python Objects

Methods are available to convert other popular python objects, such as those from RDKit

``` python
from simmate.toolkit import Molecule
from rdkit import Chem

# Smiles -> RDKit -> Simmate
rdkit_mol = Chem.MolFromSmiles("Cc1ccccc1")
molecule = Molecule.from_rdkit(rdkit_mol)
# !!! NOT RECOMMENDED !!!

# Smiles -> Simmate 
molecule = Molecule.from_smiles("Cc1ccccc1")
# !!! RECOMMENDED !!!
```

| TYPE                                   | METHOD                        |
| -------------------------------------- | ----------------------------- |
| RDKit Mol object                       | `from_rdkit`                  |
| RDKit Mol object written as binary     | `from_binary`                 |
| Simmate (aka nothing needs to be done) | `from_dynamic`                |
| `pathlib.Path`                         | see `from_file` section above |

--------------------------------------------------------------------------------

### Database Entries

!!! warning
    Loading from database metadata is still in progress. Refer to our guides on Python ORM 
    to access datasets as `Molecule` objects quickly.

    For example:
    ``` python
    from simmate.database import connect
    from simmate.datasets.models import CortevaCore

    molecule_db = CortevaCore.objects.get(id=123)
    molecule = molecule_db.to_toolkit()
    ```

--------------------------------------------------------------------------------