# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit.validators.base import Validator


class SiteDistance(Validator):
    def __init__(self, distance_cutoff):

        self.distance_cutoff = distance_cutoff

    def check_structure(self, structure):

        # check the min distance of sites

        # ignore the diangonal (which is also made of zeros)
        dm = structure.distance_matrix
        nonzeros = dm[numpy.nonzero(dm)]
        min_distance = nonzeros.min()

        # check if min is larger than a tolerance
        check = min_distance >= self.distance_cutoff

        return check
