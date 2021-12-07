# -*- coding: utf-8 -*-

# For adding new selection methods, DEAP is a good reference:
#   https://github.com/DEAP/deap/blob/master/deap/tools/selection.py
#   https://deap.readthedocs.io/en/master/api/tools.html
#
# Their selection methods take a list of individuals that each have a .fitness
# attribute. Instead, I pass individuals here as a pandas dataframe and have
# them specify a "fitness_column"
#
# Another good reference is Wikipedia
#   https://en.wikipedia.org/wiki/Selection_(genetic_algorithm)

# NOTE: I assume lower fitness is better! This may change in the future because
# other selection methods throw issues with lower=better and even more issues
# when we have negative values


class Selector:
    def __init__(
        self,
    ):
        # add any unchanging variables or settings here
        pass

    def select(self, nselect, individuals, fitness_column):
        # The select method should take in two arguments:
        # individuals = a pandas dataframe with columns "id" and "fitness"
        # n = the number of individuals that we want to choose from those fitnesses
        # The select method should then return a list/tuple of the indicies
        # of the fitnesses that were selected
        pass


class TruncatedSelection:
    """
    Truncated selection limits the parent selection to the top X% of individuals,
    and then within this top section, every individual has an equal chance of
    being selected.
    """

    def __init__(self, percentile=0.05, ntruncate_min=5, allow_duplicate=True):

        # aim to grab this percent of individuals
        self.percentile = percentile

        # at minimum, make sure we can select from this number of best individuals
        self.ntruncate_min = ntruncate_min

        # whether we can select the same individual more than once
        self.allow_duplicate = allow_duplicate

    def select(self, nselect, individuals, fitness_column):

        # truncate the population to those with energies in the lowest X%. This
        # value should be greater or equal to our minimum set above
        ntruncate = int(len(individuals) * self.percentile)
        if ntruncate < self.ntruncate_min:
            ntruncate = self.ntruncate_min

        # limit our potential selection to the top X% and then randomly select
        # the correct number of parents
        df_truncated = individuals.nsmallest(ntruncate, fitness_column)
        df_parents = df_truncated.sample(nselect, replace=self.allow_duplicate)

        # return the list of indexes to be selected
        return df_parents
