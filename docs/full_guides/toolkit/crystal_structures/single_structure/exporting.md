# Exporting Structures

--------------------------------------------------------------------------------

## Overview

Simmate's `Structure` class provides simple and flexible methods for exporting your data to common formats, including file-based outputs, standard Python objects, and visualization-ready formats.

--------------------------------------------------------------------------------

## Files

To write a structure to a file, use the `to` method. Simmate supports all formats that PyMatGen does.

``` python
from simmate.toolkit import Structure

# read a structure
structure = Structure.from_file("example.cif")

# write it back to a new file and format
structure.to(filename="my_new_file.poscar", fmt="poscar")
```

Commonly supported formats:

-   CIF
-   POSCAR
-   CSSR
-   JSON (via `to_json`)

--------------------------------------------------------------------------------

## Visualization

### Three.js JSON

Simmate includes a specialized method for exporting structure data in a JSON format designed for rendering with Three.js. This is the same format used for the visualizations on the Simmate website.

``` python
# Generate JSON for Three.js rendering
json_data = structure.to_threejs_json(
    add_edge_elements=True,
    bonding_method="CrystalNN",
    sanitize=True,
)
```

--------------------------------------------------------------------------------

## Python Objects

### Dictionaries and JSON

You can export a structure to a standard Python dictionary or a JSON string for easy storage or transfer.

``` python
# Export as a dictionary
structure_dict = structure.as_dict()

# Export as a JSON string
structure_json = structure.to_json()
```

### ASE Atoms

For integration with the Atomic Simulation Environment (ASE), Simmate provides a converter.

``` python
# Coming soon: easier conversion!
# For now, you can use the ASE adapter directly:
from simmate.toolkit.file_converters import AseAtomsAdaptor
ase_atoms = AseAtomsAdaptor.get_atoms(structure)
```

--------------------------------------------------------------------------------
