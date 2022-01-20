# -*- coding: utf-8 -*-

from simmate.toolkit.transformations.base import Transformation


class CoordinateOrderedPerturbation(Transformation):

    # known as "coordinate mutation" in USPEX
    # site locations are mutated where sites with lower order have higher preference for mutation
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf
    # ""Coordinate mutation was found [2] to be ineffective, because “blind” displacement of the
    # atoms is much more likely to decrease the quality of a structure than to increase it.""
    #!!! because of the quote above, the coordinate displacement is order-dependent

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
    ):
        pass

    def apply_transformation(self, structure, max_attempts=100):
        return
