# -*- coding: utf-8 -*-

"""
This module defines the Structure class.

It is a very basic extension PyMatGen's core Structure class, as it only adds
a few extra methods and does not change any other usage.
"""

from pathlib import Path

from pymatgen.core import Structure as PymatgenStructure


class Structure(PymatgenStructure):
    # Leave docstring blank and just inherit from pymatgen

    database_object = None  # simmate.database.base_data_types.Structure
    """
    If this structure came from a `simmate.database.base_data_types.Structure`
    object, then this attribute will be set to the original database object.
    
    Otherwise, this will be left as `None`.
    """
    # Note, we don't set the type here because it is a cross-module dependency
    # that is frequently not required

    _source: dict = {}  # the default source is none

    @property
    def source(self) -> dict:
        """
        Where the structure came from. Typically, the source is just the
        database entry that the structure was loaded from. For more complex
        origins (e.g. a structure mutation or prototype), this property can
        also be set dynamically in other methods.
        """
        if self._source:
            return self._source
        elif self.database_object:
            return self.database_object.to_dict()
        else:
            return {}

    @source.setter
    def source(self, new_value: dict):
        # this method just lets us override the property method above
        # https://stackoverflow.com/questions/1684828/
        self._source = new_value

    def get_sanitized_structure(self):
        """
        Run symmetry analysis and "sanitization" on the pymatgen structure
        """

        # Make sure we have the primitive unitcell first
        # We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
        # built-in Structure.get_primitive_structure function:
        #   structure = structure.get_primitive_structure(0.1) # Default tol is 0.25

        # Default tol is 0.01, but we use a looser 0.1 Angstroms
        # from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        # structure_primitive = SpacegroupAnalyzer(structure, 0.1).find_primitive()
        # BUG: with some COD structures, this symm analysis doesn't work. I need
        # to look into this more and figure out why.

        # Default tol is 0.25 Angstroms
        structure_primitive = self.get_primitive_structure()

        # Convert the structure to a "sanitized" version.
        # This includes...
        #   (i) an LLL reduction
        #   (ii) transforming all coords to within the unitcell
        #   (iii) sorting elements by electronegativity
        structure_sanitized = structure_primitive.copy(sanitize=True)

        # return back the sanitized structure
        return structure_sanitized

    @classmethod
    def from_dynamic(cls, structure):
        """
        This is an experimental feature.

        Possible structure formats include...
            object of toolkit structure
            dictionary of toolkit structure
            dictionary of...
                (1) python path to calculation datatable
                (2) one of the following (only one is used in this priority order):
                    (a) prefect flow id
                    (b) calculation id
                    (c) directory
                    ** these three are chosen because all three are unique for every
                    single calculation and we have access to different ones at different
                    times!
                (3) (optional) attribute to use on table (e.g. structure_final)
                    By default, we assume calculation table is also a structure table
            filename for a structure (cif, poscar, etc.) [TODO]
        """

        # if the input is already a pymatgen structure, just return it back
        if isinstance(structure, PymatgenStructure):
            structure_cleaned = structure

        # if the "@module" key is in the dictionary, then we have a pymatgen
        # structure dict which we convert to a pymatgen object and return
        elif isinstance(structure, dict) and "@module" in structure.keys():
            structure_cleaned = cls.from_dict(structure)

        # if there is a database_table key, then we are pointing to the simmate
        # database for the input structure
        elif isinstance(structure, dict) and "database_table" in structure.keys():
            structure_cleaned = cls.from_database_dict(structure)

        # if the value is a str and it relates to a filepath, then we load the
        # structure from a file.
        elif isinstance(structure, str) and Path(structure).exists():
            structure_cleaned = cls.from_file(structure)

        # from_dynamic includes a check to the database, but we don't want to
        # connect to the database unless we need to. This would slow down
        # the checks above. So instead, we check an attribute that we know is
        # on all tables instead of checking isinstance(DatabaseStructure).
        elif hasattr(structure, "table_name"):
            structure_cleaned = cls.from_database_object(structure)

        # Otherwise an incorrect format was given
        else:
            if isinstance(structure, str):
                raise FileNotFoundError(
                    "Are you trying to provide a filename as your input structure? "
                    "If so, make sure you have the proper working directory set. "
                    f"We were unable to find '{structure}' in '{Path.cwd()}'"
                )
            else:
                raise Exception(
                    "Unknown format provided for structure input. "
                    f"{type(structure)} was provided."
                )

        return structure_cleaned

    # -------------------------------------------------------------------------

    # All methods below wrap converters from the `simmate.file_converters.structure`
    # module. To keep this class modular (from the database and optional deps),
    # imports are done lazily. This means we import the relevant convert once
    # the method is called -- rather than when this module is initially loaded.

    @classmethod
    def from_database_dict(cls, structure: dict):
        from simmate.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_dict(structure)

    @classmethod
    def from_database_object(cls, structure: dict):
        from simmate.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_object(structure)

    @classmethod
    def from_database_string(cls, structure_string: str):
        from simmate.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_string(structure_string)

    # TODO: from_cif, from_poscar, from_ase, from_jarvis, etc.
    # TODO: to_cif, to_poscar, to_ase, to_jarvis, etc.
