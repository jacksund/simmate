# -*- coding: utf-8 -*-

from simmate.engine import Workflow
from simmate.toolkit import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.structure_matcher import StructureMatcher

class StructureWorkflow(Workflow):
    """
    An abstract mix-in for workflows that take a structures as parameters in
    their run_config method
    """
    
    _parameter_methods = Workflow._parameter_methods + ["_get_clean_structure"]
    
    standardize_structure: str | bool = False
    """
    In some cases, we may want to standardize the structure during our setup().
    
    This means running symmetry analysis on the structure in order to reduce
    the symmetry and also converting it to some standardized form. There
    are three different forms to choose from and thus 3 different values that
    `standardize_structure` can be set to:
    
    - `primitive`: for the standard primitive unitcell
    - `conventional`: for the standard conventional unitcell
    - `primitive-LLL`: for the standard primitive unitcell that is then LLL-reduced
    - `False`: this is the default and will disable this feature
    
    We recommend using `primitive-LLL` when the smallest possible and most cubic
    unitcell is desired.
    
    We recommend using `primitive` when calculating band structures and 
    ensuring we have a standardized high-symmetry path. Note, existing band
    structure workflows automatically adjust this value for you.
    
    To control the tolerances used to symmetrize the structure, you can use the
    symmetry_precision and angle_tolerance attributes.
    
    By default, no standardization is applied.
    """

    symmetry_precision: float = 0.01
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the sites are symmetrically equivalent. (in Angstroms)
    """

    angle_tolerance: float = 0.5
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the angles between sites are symmetrically equivalent. (in Degrees)
    """
    
    @classmethod
    def _get_clean_structure(
        cls,
        structure: Structure,
        standardize_structure: str | bool = None,
        symmetry_precision: float = None,
        angle_tolerance: float = None,
        **kwargs,
    ) -> Structure:
        """
        Uses the class attribute for `standardize_structure`. If this is set
        to any of the listed modes, then the structure unitcell is converted
        using the proper methods.

        Note, this method is typically called within `setup` before any input
        files are written. You should never have to call it directly.
        """

        # See if these values were provided, or default to class attribute.
        # We rename this to "standardize mode" to accurately descibe the
        # variable if it is set
        standardize_mode = standardize_structure or cls.standardize_structure
        symmetry_precision = symmetry_precision or cls.symmetry_precision
        angle_tolerance = angle_tolerance or cls.angle_tolerance

        # if standardize_structure is not requested, then we just return the
        # orignal input structure.
        if not standardize_mode:
            return structure

        # Make sure the user
        if standardize_mode not in ["primitive-LLL", "conventional", "primitive"]:
            raise Exception(
                f"Standardization mode {standardize_mode} is not supported."
            )

        # Both cleaning steps start with looking at the symmetry analysis
        sym_finder = SpacegroupAnalyzer(
            structure,
            symprec=symmetry_precision,
            angle_tolerance=angle_tolerance,
        )

        # If requested, we convert to the LLL-reduced unit cell, which aims to
        # be as cubic as possible.
        if standardize_mode == "primitive-LLL":
            structure_prim = sym_finder.get_primitive_standard_structure()
            structure_cleaned = structure_prim.copy(sanitize=True)
            return structure_cleaned

        # For band structures, we need to make sure the structure is in the
        # standardized primitive form.
        if standardize_mode == "primitive":
            structure_cleaned = sym_finder.get_primitive_standard_structure(
                international_monoclinic=False,
            )
            # check for pymatgen bugs here
            check_for_standardization_bugs(structure, structure_cleaned)
            return structure_cleaned

        # lastly is the conventional standard, which is used the least.
        if standardize_mode == "conventional":
            structure_cleaned = sym_finder.get_conventional_standard_structure()
            return structure_cleaned

def check_for_standardization_bugs(
    structure_original: Structure,
    structure_new: Structure,
):
    # In pymatgen, they include this code with the standardization of their
    # structures because there were several bugs in the past and they want to
    # double-check themselves. I'm still using their code to standardize
    # my structures, so I should make this check too.

    vpa_old = structure_original.volume / structure_original.num_sites
    vpa_new = structure_new.volume / structure_new.num_sites

    if abs(vpa_old - vpa_new) / vpa_old > 0.02:
        raise ValueError(
            "Standardizing failed! Volume-per-atom changed... "
            f"old: {vpa_old}, new: {vpa_new}"
        )

    sm = StructureMatcher()
    if not sm.fit(structure_original, structure_new):
        raise ValueError("Standardizing failed! Old structure doesn't match new.")
