# -*- coding: utf-8 -*-

import pandas


class Selector:
    """
    The abstract base class for selecting parent individuals from a pool. This
    class should be not used directly but inheritted from.

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

    @classmethod
    def select(
        cls,
        nselect: int,
        individuals: pandas.DataFrame,
        fitness_column: str,
    ):
        # The select method should take in two arguments:
        # individuals = a pandas dataframe with columns "id" and "fitness"
        # n = the number of individuals that we want to choose from those fitnesses
        # The select method should then return a list/tuple of the indicies
        # of the fitnesses that were selected
        raise NotImplementedError(
            "You must add a custom select method for your Selector subclass"
        )

    @classmethod
    @property
    def name(cls):
        """
        A nice string name for the selector. By default it just returns the name
        of this class.
        """
        return cls.__name__

    @classmethod
    def select_from_datatable(
        cls,
        nselect: int,
        datatable,  # Queryset
        fitness_column: str = None,
        query_limit: str = None,
    ):
        # our selectors just require a dataframe where we specify the fitness
        # column. So we query our individuals database to give this as an input.
        datatable_cleaned = datatable
        if fitness_column:
            datatable_cleaned = datatable_cleaned.order_by(fitness_column)
        if query_limit:
            datatable_cleaned = datatable_cleaned[:query_limit]

        individuals_df = datatable_cleaned.to_dataframe()

        # From these individuals, select our parent structures
        parents_df = cls.select(
            nselect=nselect,
            individuals=individuals_df,
            fitness_column=fitness_column,
        )

        # grab the id column of the parents and convert it to a list
        parent_ids = parents_df.id.values.tolist()

        # Now lets grab these structures from our database and convert them
        # to a list of pymatgen structures.
        # We have to make separate queries for this instead of doing "id__in=parent_ids".
        # This is because (1) order may be important and (2) we may have duplicate
        # entries. For example, a hereditary mutation can request parent ids of [123,123]
        # in which case we want to give the same input structure twice!
        parent_structures = [
            datatable.only("structure").get(id=parent_id).to_toolkit()
            for parent_id in parent_ids
        ]

        # When there's only one structure selected we return the structure and
        # id independently -- not within a list
        if nselect == 1:
            parent_ids = parent_ids[0]
            parent_structures = parent_structures[0]

        # for record keeping, we also want to return the ids for each structure
        return parent_ids, parent_structures
