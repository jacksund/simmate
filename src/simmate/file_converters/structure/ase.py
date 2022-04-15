# -*- coding: utf-8 -*-

"""
This converter simply imports a pymatgen class. With this you can quickly
convert between Simmate.toolkit and ASE.atoms objects.

``` python

from simmate.toolkit import Structure
from simmate.file_converters.structure.ase import AseAtomsAdaptor


initial_structure = Structure.from_file("example.cif")

# convert to ASE
new_ase_object = AseAtomsAdaptor.get_atoms(structure)

# convert back to PyMatgen/Simmate
new_toolkit_object = AseAtomsAdaptor.get_structure(new_ase_object)

# alternatively, you can convert back to PyMatgen Molecule
new_molecule_object = AseAtomsAdaptor.get_molecule(new_ase_object)
```
"""


from pymatgen.io.ase import AseAtomsAdaptor

__all__ = ["AseAtomsAdaptor"]
