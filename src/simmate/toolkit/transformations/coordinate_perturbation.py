# -*- coding: utf-8 -*-

from pymatgen.transformations.standard_transformations import (
    PerturbStructureTransformation,
)

from simmate.toolkit.transformations.base import Transformation


class CoordinatePerturbation(Transformation):

    # random perturbation of sites was removed from USPEX because primarily made more defective + lower energy structures
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    # note, the function Structure.pertrub displaces each site at an equal distance
    # this function on the other hand displaces at a variable distance selected from a guassian distribution between min/mix
    # this transformation is almost guaranteed to give a structure with P1 symmetry

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(self, min_displace=0, max_displace=1):  #!!! whats a good displacement?

        self.perturb_object = PerturbStructureTransformation(min_displace, max_displace)

    def apply_transformation(self, structure):

        new_structure = self.perturb_object.apply_transformation(structure)

        return new_structure
