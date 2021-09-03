# -*- coding: utf-8 -*-

##############################################################################

"""

A library of functions used to generate random vector coordinates based on
various probability distributions and parameters. If you want to see how a
distribution sampling looks, run the code below with replacing the 
generator you are interested in. Here's an example:
    
# pick the generator and settings you want to visualize
gen = NormallyDistributedVectors(15,20,extra_conditions=['x>=3+y'])

# generate values (here we take 10,000 samples)
values = []
for n in range(10000):
    vector = gen.new_vector() 
    for x in vector:
        values.append(x)


# plot a basic histogram using plotly offline
import plotly.express as px
fig = px.histogram(x=values)
from plotly.offline import plot
plot(fig, config={'scrollZoom': True})

"""

##############################################################################

from numpy.random import random, normal

##############################################################################

# random values between min_value and max_value that are uniformly distributed
# extra conditions can be added. ex: 'x<=2*y'
class UniformlyDistributedVectors:
    def __init__(self, min_value=0, max_value=1, extra_conditions=[]):

        self.min_value = min_value
        self.max_value = max_value
        self.extra_conditions = (
            extra_conditions  # strings that use x,y,z for vector positions. ex: 'x>=y'
        )

    def new_vector(
        self, size=3
    ):  #!!! I need to test if 'size=3' setting this slows the algorithm! Initial tests with %timeit say there's no difference

        # initiate a placeholder to see if the vector is valid against all conditions
        # and start with it set to False so we can start the while-loop
        check = False

        # run this loop until we find a valid vector
        while not check:

            # generate random 3x1 matrix where values are uniformly [0,1)
            vector = random(size)

            # shift the vector min/max boundries and scale
            vector = vector * (self.max_value - self.min_value) + self.min_value

            # check that all extra conditions are met
            # and assume it is valid until proven otherwise
            check = True
            for condition in self.extra_conditions:
                x, y, z = vector
                check = eval(condition, None, dict(x=x, y=y, z=z))
                # if the check is False, exit the for-loop
                if not check:
                    break

            # if the for-loop above 'breaks' at any point, check will be False and the while-loop will restart
            # if the for-loop goes through all extra_conditions and never breaks, check will be True and the while-loop will finish

        return vector


##############################################################################

# random values between min_value and max_value that are normally (Gaussian) distributed
# the probability curve is centered at center and has a standard deviation of standdev
# extra conditions can be added. ex: 'x<=2*y'
class NormallyDistributedVectors:
    def __init__(
        self, min_value=0, max_value=1, extra_conditions=[], center=None, standdev=None
    ):

        self.min_value = min_value
        self.max_value = max_value
        self.extra_conditions = (
            extra_conditions  # strings that use x,y,z for vector positions. ex: 'x>=y'
        )

        # Set the center of the normal (Guassian) distribution
        # if a number is provided, use it
        if center:
            self.center = center
        # if center is not set, we assume the center is at the middle of min/max values
        else:
            self.center = (max_value + min_value) / 2

        # Set the standard deviation of the normal (Guassian) distribution
        # if a number is provided, use it
        if standdev:
            self.standdev = standdev
        # if standdev is not set, we assume the standard_deviation is 1/5*(max-min)
        else:
            self.standdev = (max_value - min_value) / 5

    def new_vector(self, size=3):

        # initiate a placeholder to see if the vector is valid against all conditions
        # and assume it is not valid until proven otherwise
        check = False

        # run this loop until we find a valid vector
        while not check:

            # generate random 3x1 matrix where values are normally distributed
            vector = normal(loc=self.center, scale=self.standdev, size=size)

            # check if all values are between min/max values specified
            check = (vector.min() >= self.min_value) and (
                vector.max() <= self.max_value
            )
            # if the check is False, use 'continue' to restart the while loop
            if not check:
                continue

            # check that all extra conditions are met
            for condition in self.extra_conditions:
                x, y, z = vector
                check = eval(condition, None, dict(x=x, y=y, z=z))
                # if the check is False, exit the for-loop
                if not check:
                    break

            # if the for-loop above 'breaks' at any point, check will be False and the while-loop will restart
            # if the for-loop goes through all extra_conditions and never breaks, check will be True and the while-loop will finish

        return vector


##############################################################################
