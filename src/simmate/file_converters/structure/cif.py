# -*- coding: utf-8 -*-

"""
This converter simply imports a pymatgen class. With this you can quickly
convert between Simmate.toolkit and CIF files.

This class is built-in to the base toolkit class, so you typically can read/write
with CIFs without ever loading this module directly.

Recommended use:
``` python

from simmate.toolkit import Structure

# read a cif file
initial_structure = Structure.from_file("example.cif")

# write a cif file
initial_structure.to("cif", "my_new_file.cif")

```

For advanced use, you can interact with this class directly:

``` python
from simmate.file_converters.structure.cif import CifParser

# load from file
cif_data = CifParser("example.cif")

# then access underlying data
cif_data.get_structures()
```
"""


from pymatgen.io.cif import CifParser, CifWriter

__all__ = ["CifParser", "CifWriter"]
