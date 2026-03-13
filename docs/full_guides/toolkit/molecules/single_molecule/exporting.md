# Molecule Exportation

--------------------------------------------------------------------------------

## Introduction

After loading a molecule, you can convert it to a different format using a `to_` method of `Molecule`. 

For instance, use `to_smiles` to output a SMILES, use `to_mol2` for a MOL2 output, and use `to_rdkit` for an RDKit object.

Thus, file format conversion typically involves two steps:

1. Load using a `from_*` method
2. Export using a `to_*` method

``` python
from simmate.toolkit import Molecule

# step 1: LOAD
molecule = Molecule.from_sdf_file("example.sdf")

# step 2: EXPORT
molecule.to_png_file("output.png")
```

!!! note
    For exporting numerous molecules or handling large files, refer to our "Many Molecules" section. 

--------------------------------------------------------------------------------

## Basic Exportation

### Files

File-based outputs accept a filename as a string or a `pathlib.Path` object.

``` python
molecule = Molecule.to_sdf_file("example.sdf")
```

| TYPE           | METHOD        |
| -------------- | ------------- |
| Image          | `to_png_file` |
| SDF (aka CTAB) | `to_sdf_file` |

!!! tip
    Each of these methods has a corresponding submethod for exporting to a string, as detailed in the section below. For instance, `to_sdf` outputs a string, while `to_sdf_file` writes a `.sdf` file.

!!! warning
    Writing numerous files (with many molecules in each) can be slow using these methods. Refer to the "many molecules" section for optimized writing of thousands or millions of molecules.

--------------------------------------------------------------------------------

### Raw Text / Strings

Instead of writing to a file, you can also obtain the converted format as a python variable (string) for use elsewhere.

``` python
my_smiles = molecule.to_smiles()
```

| TYPE                 | METHOD                     |
| -------------------- | -------------------------- |
| INCHI                | `to_inchi`                 |
| INCHI Key            | `to_inchi_key`             |
| SMILES               | `to_smiles`                |
| SMILES (kekulized)   | `to_smiles(kekulize=True)` |
| SMILES (CX-extended) | `to_cx_smiles`             |
| SDF (aka CTAB)       | `to_sdf`                   |

!!! tip
    Each of these methods has a corresponding submethod for exporting directly to a file, as detailed in the section above. For instance, `to_sdf` outputs a string, while `to_sdf_file` writes a `.sdf` file.

--------------------------------------------------------------------------------

### Python Objects

Methods are available to convert to other popular python objects, such as those from RDKit.

``` python
molecule.to_rdkit()
```

| TYPE                               | METHOD      |
| ---------------------------------- | ----------- |
| RDKit Mol object                   | `to_rdkit`  |
| RDKit Mol object written as binary | `to_binary` |

--------------------------------------------------------------------------------