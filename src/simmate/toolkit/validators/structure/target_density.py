# -*- coding: utf-8 -*-

from simmate.toolkit.validators import Validator


class TargetDensity(Validator):
    """
    Check if structure density is within an acceptable range.
    """

    def __init__(
        self,
        target_density,
        percent_allowance=0.05,
        check_slab=True,
    ):
        self.target_density = target_density
        self.percent_allowance = percent_allowance
        self.check_slab = check_slab

    def check_structure(self, structure):
        density = structure.density if not self.check_slab else structure.slab_density
        if abs(density - self.target_density) / density > self.percent_allowance:
            print(density)
            return False
        return True
