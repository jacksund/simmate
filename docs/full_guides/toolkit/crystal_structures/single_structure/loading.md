# Loading Structures

--------------------------------------------------------------------------------

## Introduction

To load a structure, call the `from_file`, `from_dynamic`, or `from_str` methods of `Structure`. 

Simmate leverages PyMatGen for many of its I/O operations, but wraps them to provide a more intuitive and unified API. 

!!! tip
    `from_dynamic` is the simplest and most convenient method, as it determines the input type (file, string, dict, etc.) and calls the appropriate underlying method.

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
for new_input in [input_01, input_02, input_03]:
    structure = Structure.from_dynamic(new_input)
```

!!! note
    `from_dynamic` also checks if we already have a `Structure` object and returns it if we do.

--------------------------------------------------------------------------------

## Basic Loading

### Files

File-based inputs accept a filename as a string or a `pathlib.Path` object. Simmate's `Structure` class inherits from PyMatGen's `Structure`, so it supports all formats that PyMatGen does.

``` python
from simmate.toolkit import Structure

structure = Structure.from_file("example.cif")
```

Commonly supported formats include:

-   CIF
-   POSCAR / CONTCAR
-   CSSR
-   Netcdf (via `.cdf`)

!!! tip
    If you have a file and are unsure of the format, `from_file` (or `from_dynamic`) is usually smart enough to figure it out based on the file extension or content.

--------------------------------------------------------------------------------

### Raw text / strings

You can read a python string variable directly. This is particularly useful for small test cases or when receiving data via a network.

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

structure = Structure.from_str(poscar_str, fmt="poscar")
```

--------------------------------------------------------------------------------

### Python Objects

Since `simmate.toolkit.Structure` inherits from `pymatgen.core.Structure`, you can use them interchangeably in most cases. If you specifically need to convert a PyMatGen object to a Simmate one (to access Simmate-specific methods), you can use `from_dynamic`:

``` python
from simmate.toolkit import Structure
from pymatgen.core import Structure as PmgStructure

pmg_structure = PmgStructure.from_file("example.cif")
structure = Structure.from_dynamic(pmg_structure)
```

--------------------------------------------------------------------------------

### Python Dictionaries

Simmate (and PyMatGen) supports loading from standardized dictionaries:

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

structure = Structure.from_dict(data)
# or alternatively
structure = Structure(**data)
```

--------------------------------------------------------------------------------

### Database Entries

Simmate provides specialized methods to load structures directly from database entries or metadata.

``` python
from simmate.toolkit import Structure

# From a database dictionary (containing table_name and pk)
db_dict = {
    "database_table": "MatprojStructure",
    "database_id": 123,
}
structure = Structure.from_database_dict(db_dict)

# From a database object directly
from simmate.apps.materials_project.models import MatprojStructure
db_obj = MatprojStructure.objects.get(id=123)
structure = Structure.from_database_object(db_obj)
```

--------------------------------------------------------------------------------
