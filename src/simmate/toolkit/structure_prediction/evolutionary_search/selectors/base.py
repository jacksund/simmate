# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------

class Selector:
    def __init__(
        self,
    ):
        # add any unchanging variables or settings here
        pass

    def select(self, fitnesses, n):
        # The select method should take in two arguments:
        # fitnesses = a list of float values
        # n = the number of individuals that we want to choose from those fitnesses
        # The select method should then return a list/tuple of the indicies
        # of the fitnesses that were selected
        pass


# -----------------------------------------------------------------------------

import pandas

# See list of methods here...
# https://en.wikipedia.org/wiki/Selection_(genetic_algorithm)


class TruncatedSelection:

    # For now I implement Truncation Selection
    # This means I limit the parent selection to the top X% of population
    # and within this top section, every individual has an equal chance
    # of being selected.
    #!!! In the future, I should implement Fitness Proportionate Selection (aka Roulette Wheel Selection)
    #!!! I can also implement this in combination with Truncation Selection.

    def __init__(self, percentile=0.05, ntrunc_min=5):

        self.percentile = percentile  # aim to grab this percent of individuals
        self.ntrunc_min = (
            ntrunc_min  # at minimum select from this number of individuals
        )

    def select(self, fitnesses, n):

        if len(fitnesses) < self.ntrunc_min:
            print("You dont have enough structures to choose from!")
            return False

        # truncate the population to those with energies in the lowest X%
        ntrunc = int(len(fitnesses) * self.percentile)

        # if ntrunc is less than ntrunc_min, reset it!
        if ntrunc < self.ntrunc_min:
            ntrunc = self.ntrunc_min

        # select the parents
        df = pandas.DataFrame(fitnesses)
        df_truncated = df.nsmallest(
            ntrunc, 0
        )  # 0 is the column name, since I don't set it above
        df_parents = df_truncated.sample(n)  # select the correct number of parents
        parents_i = df_parents.index.values  # convert the index values to numpy

        # return the list of indexes to be selected
        return tuple(
            parents_i
        )  #!!! I convert to a tuple here for memory saving. In the future, I may go back to numpy for speed.


# Fully Random Selection
# randomly grab the propper number of parents from previous structures
# I grab the index here, which is easier to store in the db
# parents_i = numpy.random.choice(range(len(search.structures)),
#                                 size = n,
#                                 replace = False,
#                                 p = None,
#                                 )
# parents = [search.structures[i] for i in parents_i]