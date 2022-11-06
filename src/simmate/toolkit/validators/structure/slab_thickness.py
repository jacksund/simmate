# -*- coding: utf-8 -*-

from simmate.toolkit.validators import Validator


class SlabThickness(Validator):
    """
    Confirms the slab thickness is within a set range

    BUG: methods assume slab is orthoganal to the z axis.
    """

    def __init__(self, max_thickness):
        self.max_thickness = max_thickness

    def check_structure(self, structure):
        slab_thickness = structure.thickness_z
        if slab_thickness > self.max_thickness:
            print(f"slab_thickness = {slab_thickness}")
            return False
        return True
