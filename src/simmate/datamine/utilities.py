# -*- coding: utf-8 -*-

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer


# TODO Move this to a Simmate.Structure method in the future


def get_sanitized_structure(structure):
    """
    Run symmetry analysis and "sanitization" on the pymatgen structure
    """

    # Make sure we have the primitive unitcell first
    # We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
    # built-in Structure.get_primitive_structure function:
    #   structure = structure.get_primitive_structure(0.1) # Default tol is 0.25

    # Default tol is 0.01, but we use a looser 0.1 Angstroms
    structure_primitive = SpacegroupAnalyzer(structure, 0.1).find_primitive()

    # Convert the structure to a "sanitized" version.
    # This includes...
    #   (i) an LLL reduction
    #   (ii) transforming all coords to within the unitcell
    #   (iii) sorting elements by electronegativity
    structure_sanitized = structure_primitive.copy(sanitize=True)

    # return back the sanitized structure
    return structure_sanitized
