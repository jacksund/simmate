Structure Converters
--------------------

This module comprises converter classes for various structure file and object formats. All converters are directly linked for conversion into the `simmate.toolkit.base_data_types.structure.Structure` class. Simmate can automatically identify the file/object format you're using in most instances. Direct use of these converters is generally reserved for advanced usage or speed optimization:

Here's an example of dynamic use:

``` python
from simmate.toolkit import Structure

structure1 = Structure.from_dynamic("example.cif")

structure2 = Structure.from_dynamic("POSCAR")

structure3 = Structure.from_dynamic(
    {"database_table": "MITStaticEnergy", "database_id": 1}
)
```

To convert between formats (for example, CIF to POSCAR), follow this two-step process:

``` python
from simmate.toolkit import Structure

# STEP 1: convert to simmate
structure = Structure.from_dynamic("example.cif")

# STEP 2: convert to the desired format
structure.to(fmt="poscar", filename="POSCAR")
```

## Additional Converters

This module does not include all the file-converters available in Simmate. You can find other converters in the `apps` module, where they are associated with a specific program. For example, the converter for POSCAR files is derived from the VASP software, so the POSCAR converter is located in the `vasp.inputs.poscar` module. Here's a list of other structure converters for your reference: 

- POSCAR (`simmate.apps.vasp.inputs.poscar`)