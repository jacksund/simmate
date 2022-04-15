# -*- coding: utf-8 -*-

"""
This converter simply imports a pymatgen class. With this you can quickly
convert between Simmate.toolkit and JARVIS.atoms objects.

``` python
from simmate.toolkit import Structure
from simmate.file_converters.structure.jarvis import JarvisAtomsAdaptor


initial_structure = Structure.from_file("example.cif")

# convert to JARVIS
new_jarvis_object = JarvisAtomsAdaptor.get_atoms(structure)

# convert back to PyMatgen/Simmate
new_toolkit_object = JarvisAtomsAdaptor.get_structure(new_jarvis_object)

# alternatively, you can convert back to PyMatgen Molecule
new_molecule_object = JarvisAtomsAdaptor.get_molecule(new_jarvis_object)
```
"""


from pymatgen.io.jarvis import JarvisAtomsAdaptor

__all__ = ["JarvisAtomsAdaptor"]
