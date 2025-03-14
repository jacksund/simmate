# Loading Structures

!!! danger
    The simmate toolkit is still in early development and not ready for use. Stick to the "PyMatgen Help" section for now.

--------------------------------------------------------------------------------

## Introduction

To load a structure, call a `from_` method of `Structure`. 

For instance, `from_cif` for a CIF input, `from_poscar` for a POSCAR input, and `from_pymatgen` for a PyMatGen object. Choose the method that corresponds to your input type, or use the `from_dynamic` strategy if you're unsure or have a variety of input types.

!!! tip
    `from_dynamic` is the simplest and most convenient method, but it may not always work! If you know your structure's format, use the specific method for it.

--------------------------------------------------------------------------------

## Dynamic Loading

Dynamic loading examines your input and determines how to convert it into a `Structure` object. It performs checks and then calls one of the methods detailed on this page.

``` python
from simmate.toolkit import Structure

# try loading from a variety of formats
input_01 = "example.cif"
input_02 = "POSCAR" 
input_03 = {
    "lattice": [
        [3.48543651, 0.0, 2.01231771],
        [1.16181217, 3.28610106, 2.01231771],
        [0.0, 0.0, 4.02463542],
    ],
    "species": ["Na", "Cl"],
    "coords": [
        [0.0000, 0.0000, 0.0000],
        [0.5000, 0.5000, 0.5000],
    ],
}

# `from_dynamic` will determine the format and convert it
for new_input in [input_01, input_02, input_03]
    structure = Structure.from_dynamic(new_input)
```

!!! note
    `from_dynamic` also checks if we already have a `Structure` object and returns it if we do.

--------------------------------------------------------------------------------

## Basic Loading

### Files

File-based inputs accept a filename as a string or a `pathlib.Path` object.

``` python
from simmate.toolkit import Structure

structure = Structure.from_cif_file("example.sdf")
```

| TYPE               | METHOD              |
| ------------------ | ------------------- |
| (dynamic loading)  | `from_file`         |
|                    |                     |
| CIF                | `from_cif_file`     |
| CSSR               | `from_cssr_file`    |
| Netcdf             | `from_cdf_file`     |
|                    |                     |
| POSCAR (& CONTCAR) | `from_poscar_file`  |
| CHGCAR             | `from_chgcar_file`  |
| LOCPOT             | `from_locpot_file`  |
| vasprun.xml        | `from_vasprun_file` |

!!! tip
    Each of these methods has a corresponding submethod for loading this format directly from text/str, detailed in the section below. For instance, `from_cif` takes a string, while `from_cif_file` takes a `.cif` file.

--------------------------------------------------------------------------------

### Raw text / strings

You can read a python string variable directly. These methods are primarily used for testing and debugging.

``` python
from simmate.toolkit import Structure

poscar_str = """
Na1 Cl1
1.0
3.485437 0.000000 2.012318
1.161812 3.286101 2.012318
0.000000 0.000000 4.024635
Na Cl
1 1
direct
0.000000 0.000000 0.000000 Na
0.500000 0.500000 0.500000 Cl
"""

structure = Structure.from_poscar(poscar_str)
```

| TYPE               | METHOD         |
| ------------------ | -------------- |
| CIF                | `from_cif`     |
| CSSR               | `from_cssr`    |
| Netcdf             | `from_cdf`     |
|                    |                |
| POSCAR (& CONTCAR) | `from_poscar`  |
| CHGCAR             | `from_chgcar`  |
| LOCPOT             | `from_locpot`  |
| vasprun.xml        | `from_vasprun` |

!!! tip
    Each of these methods has a corresponding submethod for loading this format directly from a file, detailed in the section above. For instance, `from_cif` takes a string, while `from_cif_file` takes a `.cif` file.

--------------------------------------------------------------------------------

### Python Objects

Methods are available to convert other popular python objects, such as those from PyMatGen:

``` python
from simmate.toolkit import Structure
from pymatgen import Structure as PmgStructure

# CIF -> PyMatGen -> Simmate [[ NOT RECOMMENDED ]]
pmg_structure = PmgStructure.from_file("example.cif")
structure = Structure.from_pymatgen(pmg_structure)

# CIF -> Simmate  [[ RECOMMENDED ]]
structure = Structure.from_file("example.cif")
```

| TYPE                        | METHOD                        |
| --------------------------- | ----------------------------- |
| PyMatGen `Structure` object | `from_pymatgen`               |
| ASE `Atoms` object          | `from_ase`                    |

--------------------------------------------------------------------------------

### Python Dictionaries

!!! warning
    Loading from python dictionaries is still in progress.

    For now, do the following:

    ``` python
    from simmate.toolkit import Structure

    data = {
        "lattice": [
            [3.48543651, 0.0, 2.01231771],
            [1.16181217, 3.28610106, 2.01231771],
            [0.0, 0.0, 4.02463542],
        ],
        "species": ["Na", "Cl"],
        "coords": [
            [0.0000, 0.0000, 0.0000],
            [0.5000, 0.5000, 0.5000],
        ],
    }

    structure = Structure(**data)
    ```

--------------------------------------------------------------------------------

### Database Entries

!!! warning
    Loading from database metadata is still in progress. Refer to our guides on Python ORM 
    to access datasets as `Structure` objects quickly.

    For example:
    ``` python
    from simmate.database import connect
    from simmate.apps.materials_project.models import MatprojStructure

    structure_db = MatprojStructure.objects.get(id=123)
    structure = structure_db.to_toolkit()
    ```

--------------------------------------------------------------------------------