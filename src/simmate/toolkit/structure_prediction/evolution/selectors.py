# -*- coding: utf-8 -*-

"""
For adding new selection methods, DEAP is a good reference:
  https://github.com/DEAP/deap/blob/master/deap/tools/selection.py
  https://deap.readthedocs.io/en/master/api/tools.html

Their selection methods take a list of individuals that each have a .fitness
attribute. Instead, I pass individuals here as a pandas dataframe and have
them specify a "fitness_column"

Another good reference is Wikipedia
  https://en.wikipedia.org/wiki/Selection_(genetic_algorithm)

NOTE: I assume lower fitness is better! This may change in the future because
other selection methods throw issues with lower=better and even more issues
when we have negative values
"""


class Selector:
    def select(self, nselect, individuals, fitness_column):
        # The select method should take in two arguments:
        # individuals = a pandas dataframe with columns "id" and "fitness"
        # n = the number of individuals that we want to choose from those fitnesses
        # The select method should then return a list/tuple of the indicies
        # of the fitnesses that were selected
        raise NotImplementedError()

    def select_from_datatable(
        self,
        nselect,
        datatable,
        ranking_column: str = None,
        query_limit: str = None,
    ):

        # our selectors just require a dataframe where we specify the fitness
        # column. So we query our individuals database to give this as an input.
        datatable_cleaned = datatable
        if ranking_column:
            datatable_cleaned = datatable_cleaned.order_by(ranking_column)
        if query_limit:
            datatable_cleaned = datatable_cleaned[:query_limit]
        individuals_df = datatable_cleaned.to_dataframe()
        # NOTE: I assume we'll never need more than the best 200 structures, which
        # may not be true in special cases.

        # From these individuals, select our parent structures
        parents_df = self.select(nselect, individuals_df, ranking_column)

        # grab the id column of the parents and convert it to a list
        parent_ids = parents_df.id.values.tolist()

        # Now lets grab these structures from our database and convert them
        # to a list of pymatgen structures.
        # We have to make separate queries for this instead of doing "id__in=parent_ids".
        # This is because (1) order may be important and (2) we may have duplicate
        # entries. For example, a hereditary mutation can request parent ids of [123,123]
        # in which case we want to give the same input structure twice!
        parent_structures = [
            datatable.only("structure_string").get(id=parent_id).to_toolkit()
            for parent_id in parent_ids
        ]

        # When there's only one structure selected we return the structure and
        # id independently -- not within a list
        if nselect == 1:
            parent_ids = parent_ids[0]
            parent_structures = parent_structures[0]

        # for record keeping, we also want to return the ids for each structure
        return parent_ids, parent_structures


class TruncatedSelection(Selector):
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
