# -*- coding: utf-8 -*-

from pymatgen.transformations.standard_transformations import (
    PerturbStructureTransformation,
)

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class CoordinatePerturbation(Transformation):
    """
    Randomly perturbs or "rattles" atomic sites within a structure. This
    transformation is almost guaranteed to give a structure with P1 symmetry.

    This is a wrapper around pymatgen's
    [PerturbStructureTransformation](https://pymatgen.org/pymatgen.transformations.standard_transformations.html#pymatgen.transformations.standard_transformations.PerturbStructureTransformation)

    NOTE: Random perturbation of sites was removed from USPEX because primarily made
    more defective + lower energy structures
    https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    NOTE: the function Structure.pertrub displaces each site at an equal distance
    this function on the other hand displaces at a variable distance selected
    from a guassian distribution between min/mix
    """

    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        min_displace: float = 0,
        max_displace: float = 1,
    ):
        perturb_object = PerturbStructureTransformation(min_displace, max_displace)

        new_structure = perturb_object.apply_transformation(structure)

        return new_structure
