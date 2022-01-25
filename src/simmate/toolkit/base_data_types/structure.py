# -*- coding: utf-8 -*-

"""
This module defines the Structure class.

It is a very basic extension PyMatGen's core Structure class, as it only adds
a few extra methods and does not change any other usage.
"""

from pymatgen.core import Structure as PymatgenStructure


class Structure(PymatgenStructure):
    # Leave docstring blank and just inherit from pymatgen

    def get_sanitized_structure(self):
        """
        Run symmetry analysis and "sanitization" on the pymatgen structure
        """

        # TODO Move this to a Simmate.Structure method in the future

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
