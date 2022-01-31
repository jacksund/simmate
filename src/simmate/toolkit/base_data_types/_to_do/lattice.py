# -*- coding: utf-8 -*-

# OPTIMIZE: using caching improves speed significantly at the cost of memory. I
# need to see which is preferable in higher-level tests.
from functools import cached_property

import numpy
from numba import njit as numba_speedup


class Lattice:
    """
    This class is for 3D crystal lattices, which are represented by a 3x3 matrix.
    This class provides a bunch of tools to pull out common values like vector
    lengths and angles, and also allows for lattice conversions.

    For some basic formulas and introduction, see here:
        http://gisaxs.com/index.php/Unit_cell
        http://gisaxs.com/index.php/Lattices
    """

    def __init__(self, matrix):
        """
        Create a lattice from a 3x3 matrix. Each vector is defined via xyz on
        one row of the matrix. For example, a cubic lattice where all vectors
        are 1 Angstrom and 90deg from eachother would be defined as
            matrix = [[1, 0, 0],
                      [0, 1, 0],
                      [0, 0, 1]]
        """

        # Convert the matrix to a numpy array and store it
        self.matrix = numpy.array(matrix)

    @cached_property
    def lengths(self):
        """
        Gives the lengths of the lattice as (a, b, c).
        """
        # The easiest way to do this is with numpy via...
        #   lengths = numpy.linalg.norm(matrix, axis=1)
        # However, we instead write a super-optimized numba function to make this
        # method really fast. This is defined below as a static method.
        # The length of a 3D vector (xyz) is defined by...
        #   length = sqrt(a**2 + b**2 + c**2)
        # and we are doing this for all three vectors at once.
        return self._lengths_fast(self.matrix)

    @staticmethod
    @numba_speedup(cache=True)
    def _lengths_fast(matrix):

        # NOTE: users should not call this method! Use lattice.lengths instead

        # OPTIMIZE: is there an alternative way to write this that numba will
        # run faster?

        #   numpy.linalg.norm(matrix, axis=1) --> doesn't work with numba
        return numpy.sqrt(numpy.sum(matrix**2, axis=1))

    @property
    def a(self):
        """
        The length of the lattice vector "a" (in Angstroms)
        """
        return self.lengths[0]

    @property
    def b(self):
        """
        The length of the lattice vector "b" (in Angstroms)
        """
        return self.lengths[1]

    @property
    def c(self):
        """
        The length of the lattice vector "c" (in Angstroms)
        """
        return self.lengths[2]

    @cached_property
    def angles(self):
        """
        The angles of the lattice as (alpha, beta, gamma).
        """
        # The angle between two 3D vectors (xyz) is defined by...
        #   angle_radians = arccos(dot(vector1, vector2)/(vector1.length*vector2.length))
        # And alpha, beta, gamma are just the angles between the b&c, a&c, and a&b
        # vectors, respectively. We cacluate all of these at once here. We also
        # write a super-optimized numba function to make this method really fast.
        # This is defined below as a static method.
        return self._angles_fast(self.matrix, self.lengths)

    @staticmethod
    @numba_speedup(cache=True)
    def _angles_fast(matrix, lengths):

        # NOTE: users should not call this method! Use lattice.angles instead

        # OPTIMIZE: is there an alternative way to write this that numba will
        # run faster?

        # keep a list of the angles
        angles = []

        # this establishes the three angles we want to calculate
        #   alpha --> angle between b and c
        #   beta --> angle between a and c
        #   gamma --> angle between a and b
        # So the numbers below are indexes of the matrix!
        # (for example, vector b has index 1)
        vector_pairs = [(1, 2), (0, 2), (0, 1)]

        # The angle between two 3D vectors (xyz) is defined by...
        #   angle_radians = arccos(dot(vector1, vector2)/(vector1.length*vector2.length))
        for vector_index_1, vector_index_2 in vector_pairs:
            # calculate single angle using formula
            unit_vector_1 = matrix[vector_index_1] / lengths[vector_index_1]
            unit_vector_2 = matrix[vector_index_2] / lengths[vector_index_2]
            dot_product = numpy.dot(unit_vector_1, unit_vector_2)
            angle = numpy.arccos(dot_product)
            # convert to degrees before saving
            angles.append(numpy.degrees(angle))

        # return the list as a numpy array
        return numpy.array(angles)

    @property
    def alpha(self):
        """
        The angle between the lattice vectors b and c (in degrees).
        """
        return self.angles[0]

    @property
    def beta(self):
        """
        The angle between the lattice vectors a and c (in degrees).
        """
        return self.angles[1]

    @property
    def gamma(self):
        """
        The angle between the lattice vectors a and b (in degrees).
        """
        return self.angles[2]
