
Structure Converters
--------------------

This module hosts converter classes for common structure file and object formats. All converters are linked directly for conversion into the `simmate.toolkit.base_data_types.structure.Structure` class. Note, in the majority of cases, you can have Simmate attempt to figure out the file/object format you have. Using these converters directly is really only needed for advanced use or speed optimization:

Example dynamic use:

``` python
from simmate.toolkit import Structure

structure1 = Structure.from_dynamic("example.cif")

structure2 = Structure.from_dynamic("POSCAR")

structure3 = Structure.from_dynamic(
    {"database_table": "MITStaticEnergy", "database_id": 1}
)
```

If you'd like to convert between formats (such as CIF --> POSCAR), you should treat this a two-step process:

``` python
from simmate.toolkit import Structure

# STEP 1: convert to simmate
structure = Structure.from_dynamic("example.cif")

# STEP 2: convert to desired format
structure.to(fmt="poscar", filename="POSCAR")
```

## Other Converters

This module does not host all file-converters that Simmate has. Others can be found in the `calculators` module, where they are associated with a specific program. For example, the converter for POSCAR files is directly from the VASP software -- therefore, you can find the POSCAR converter in the `vasp.inputs.poscar` module. Here is a list of other structure converters for reference: 

- POSCAR (`simmate.calculators.vasp.inputs.poscar`)
