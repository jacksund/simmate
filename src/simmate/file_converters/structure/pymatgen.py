"""
This module provides conversion between the Simmate ToolkitStructure object and 
pymatgen Structure objects. Because our toolkit class inherits from pymatgen,
this feature should rarely (if ever) be used.

``` python
from simmate.toolkit import Structure
from simmate.file_converters.structure.pymatgen import PyMatGenAdapter


initial_structure = Structure.from_file("example.cif")

# convert to PyMatgen
new_pmg_object = PyMatGenAdapter.get_pymatgen(structure)

# convert back to PyMatgen/Simmate
new_toolkit_object = PyMatGenAdapter.get_toolkit(new_pmg_object)
```
"""

from simmate.toolkit import Structure as ToolkitStructure
from pymatgen.core.structure import Structure as PyMatGenStructure


class PyMatGenAdapter:
    """
    Adaptor for conversion between the Simmate ToolkitStructure object and
    pymatgen Structure objects.
    """

    @staticmethod
    def get_pymatgen(structure: ToolkitStructure) -> PyMatGenStructure:
        """
        Returns PyMatGen Structure object from Simmate Structure object.
        """
        data = structure.as_dict()
        return PyMatGenStructure.from_dict(data)

    @staticmethod
    def get_toolkit(structure: PyMatGenStructure) -> ToolkitStructure:
        """
        Returns PyMatGen Structure object from Simmate Structure object.
        """
        data = structure.as_dict()
        return ToolkitStructure.from_dict(data)
