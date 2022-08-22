# -*- coding: utf-8 -*-

from simmate.toolkit.transformations.base import Transformation


class CoordinateOrderedPerturbation(Transformation):
    """
    (NOT YET IMPLEMENTED: THIS IS A PLACEHOLDER)

    Known as "coordinate mutation" in USPEX. Here, site locations are mutated
    where sites with lower order have higher preference for mutation
        https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    From one of their papers:
    > Coordinate mutation was found [2] to be ineffective, because “blind”
      displacement of the atoms is much more likely to decrease the quality
      of a structure than to increase it.
    """

    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False
