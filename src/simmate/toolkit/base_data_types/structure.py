# -*- coding: utf-8 -*-

"""
This module defines the Structure class.

It is a very basic extension PyMatGen's core Structure class, as it only adds
a few extra methods and does not change any other usage.
"""

import itertools
from pathlib import Path

import numpy
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

    # All methods below wrap converters from the `simmate.toolkit.file_converters.structure`
    # module. To keep this class modular (from the database and optional deps),
    # imports are done lazily. This means we import the relevant convert once
    # the method is called -- rather than when this module is initially loaded.

    @classmethod
    def from_database_dict(cls, structure: dict):
        from simmate.toolkit.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_dict(structure)

    @classmethod
    def from_database_object(cls, structure: dict):
        from simmate.toolkit.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_object(structure)

    @classmethod
    def from_database_string(cls, structure_string: str):
        from simmate.toolkit.file_converters.structure.database import DatabaseAdapter

        return DatabaseAdapter.get_toolkit_from_database_string(structure_string)

    # TODO: from_cif, from_poscar, from_ase, from_jarvis, etc.
    # TODO: to_cif, to_poscar, to_ase, to_jarvis, etc.

    # -------------------------------------------------------------------------

    def to_json_threejs(self):
        return {
            "lattice": self.lattice.matrix.tolist(),
            "sites": self._serialize_sites_for_threejs(),
            "bonds": [],  # TODO
        }

    def _serialize_sites_for_threejs(self):
        # TODO: handle unordered structures (self.is_ordered=False)

        # We collect all sites to draw here. Each one is this list will be a tuple
        # of... (element_symbol, radius, cartesian_coordinates)
        # For example, ("Na", 0.75, [0.5, 0.5, 0.5])

        sites_to_draw = []
        lattice_matrix = self.lattice.matrix

        # for each site in the structure, we want to gather all site coordinates
        # that we want to display. Note this is more than just structure.cart_coords
        # Because we want symmetrical equivalents that are also on the cell axes.
        # For example, if there a site at (0,0,0) then we also want to display the
        # site at (1,1,1).
        for site in self:

            # Grab the base info that is the same for all site images here.
            radius = 0.75
            element = site.specie.symbol
            # TODO: We fix the radius for now but may do oxidation analysis for
            # accurate ionic radii in the future

            # first store this base site to our site collection.
            sites_to_draw.append((element, radius, site.coords.tolist()))

            # If a site has a fractional coordinate that is close to zero, then
            # that means we should duplicate the site along that edge of the lattice.
            # For example, (0, 0.5, 0.5) should be duplicated along the a-vector
            # and thus add the site (1, 0.5, 0.5).
            # We do this by checking the fractional coordinates and seeing if each
            # is close to 0.
            zero_elements = [
                i
                for i, x in enumerate(site.frac_coords)
                if numpy.isclose(x, 0, atol=0.05)
            ]

            # If more than one value is close to zero, then we need to add multiple
            # duplicate sites. For example, (0,0,0.5) would need us to add
            # (0, 1, 0.5), (1, 0, 0.5), and (1, 1, 0.5). So here we go through
            # and find all permutations that we need to add.
            permutatons = [
                combination
                for n in range(1, len(zero_elements) + 1)
                for combination in itertools.combinations(zero_elements, n)
            ]

            # Now let's iterate through each permutation and add it to our sites list
            for permutaton in permutatons:
                # make the vector that we need to add to the base site. For example,
                # if the permutation is (0,2) then we would do...
                # coords + [1, 0, 1]. Note I use fractional coords in this example
                # but use cartesians coords below.
                shift_vector = numpy.zeros(3)
                for x in permutaton:
                    shift_vector = numpy.add(shift_vector, lattice_matrix[x])
                new_coords = site.coords + shift_vector
                sites_to_draw.append((element, radius, new_coords.tolist()))

            # We now repeat the above process but now with sites that have coordinate
            # that are close to 1. The key difference here is that we subract 1 instead
            # of adding 1 like we did above. e.g (1, 0.5, 0.5) becomes (0, 0.5, 0.5)
            zero_elements = [
                i
                for i, x in enumerate(site.frac_coords)
                if numpy.isclose(x, 1, atol=0.05)
            ]
            permutatons = [
                combination
                for n in range(1, len(zero_elements) + 1)
                for combination in itertools.combinations(zero_elements, n)
            ]
            for permutaton in permutatons:
                shift_vector = numpy.zeros(3)
                for x in permutaton:
                    shift_vector = numpy.subtract(shift_vector, lattice_matrix[x])
                new_coords = site.coords + shift_vector
                sites_to_draw.append((element, radius, new_coords.tolist()))

        # # Add bonded sites outside of unticell
        # # Two issues exist for this code:
        # #    1. doesn't find bonded sites to atoms that were duplicated along edges
        # #    2. duplicate atoms are added to sites_to_draw
        # structure_graph = CrystalNN().get_bonded_structure(structure)
        # for n in range(len(structure_graph.structure)):
        #    connected_sites = structure_graph.get_connected_sites(n)
        #    for connected_site in connected_sites:
        #        if connected_site.jimage != (0, 0, 0):
        #            sites_to_draw.append(connected_site.site.coords)

        return sites_to_draw
