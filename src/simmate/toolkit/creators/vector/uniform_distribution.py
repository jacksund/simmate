# -*- coding: utf-8 -*-

from numpy.random import random as numpy_random


class UniformlyDistributedVectors:
    # This class creates random coordinates (x,y,z) that follow a uniform distribution.
    # The random values will between min_value and max_value, and also
    # extra conditions can be added. For example, ['x>=y', 'x<z*2', 'y<z+1'].

    def __init__(self, min_value=0, max_value=1, extra_conditions=[]):

        # Extra conditions should be a list of strings that use x,y,z for vector
        # positions. For example, ['x>=y', 'x<z*2', 'y<z+1']

        self.min_value = min_value
        self.max_value = max_value
        self.extra_conditions = extra_conditions

    def new_vector(self):

        # We want to attempt to make a vector until it meets all of the conditions
        # that we set above. We therefore have a while loop. To start the whileloop,
        # we need this conditon set to false
        is_valid_vector = False
        while not is_valid_vector:

            # generate random 3x1 matrix where values are uniformly [0,1)
            vector = numpy_random(3)

            # This vector is from 0 to 1 right now, so we shift the vector
            # within the min/max boundries and scale it within this range.
            vector = vector * (self.max_value - self.min_value) + self.min_value

            # check that all extra conditions are met and assume it is valid
            # until proven otherwise.
            is_valid_vector = True
            for condition in self.extra_conditions:
                x, y, z = vector
                is_valid_vector = eval(condition, None, dict(x=x, y=y, z=z))
                # If this condition isn't met (check=False), then we can exit
                # the loop and try with a new vector
                if not is_valid_vector:
                    break

            # If the for-loop above 'breaks' at any point, check will be False
            # and the while-loop will restart. If the for-loop goes through all
            # extra_conditions and never breaks, check will be True and the
            # while-loop will finish

        return vector
