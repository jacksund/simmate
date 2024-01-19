# Exporting Structures

--------------------------------------------------------------------------------

## Introduction

After loading a molecule, you can convert it to a different format using a `to_` method of `Structure`. 

For instance, use `to_cif` to output a CIF, use `to_poscar` for a POSCAR output, and use `to_pymatgen` for a PyMatGen object.

Thus, file format conversion typically involves two steps:

1. Load using a `from_*` method
2. Export using a `to_*` method

``` python
from simmate.toolkit import Structure

# step 1: LOAD
structure = Structure.from_cif_file("example.cif")

# step 2: EXPORT
structure.to_poscar_file("POSCAR")
```

!!! note
    For exporting numerous structures or handling large files, refer to our "Many Structures" section. 

--------------------------------------------------------------------------------

## Basic Exportation

### Files

File-based outputs accept a filename as a string or a `pathlib.Path` object.

``` python
structure = Structure.to_cif_file("example.cif")
```

| TYPE               | METHOD           |
| ------------------ | ---------------- |
| CIF                | `to_cif_file`    |
| POSCAR (& CONTCAR) | `to_poscar_file` |

!!! tip
    Each of these methods has a corresponding submethod for exporting to a string, as detailed in the section below. For instance, `to_cif` outputs a string, while `to_cif_file` writes a `.cif` file.

!!! warning
    Writing numerous files (with many structures in each) can be slow using these methods. Refer to the "many structures" section for optimized writing of thousands or millions of structures.

--------------------------------------------------------------------------------

### Raw Text / Strings

Instead of writing to a file, you can also obtain the converted format as a python variable (string) for use elsewhere.

``` python
poscar_str = structure.to_poscar()
```

| TYPE               | METHOD      |
| ------------------ | ----------- |
| CIF                | `to_cif`    |
| POSCAR (& CONTCAR) | `to_poscar` |

!!! tip
    Each of these methods has a corresponding submethod for exporting directly to a file, as detailed in the section above. For instance, `to_cif` outputs a string, while `to_cif_file` writes a `.cif` file.

--------------------------------------------------------------------------------

### Python Objects

Methods are available to convert to other popular python objects, such as those from RDKit.

``` python
molecule.to_rdkit()
```

| TYPE                        | METHOD        |
| --------------------------- | ------------- |
| PyMatGen `Structure` object | `to_pymatgen` |
| ASE `Atoms` object          | `to_ase`      |

--------------------------------------------------------------------------------
