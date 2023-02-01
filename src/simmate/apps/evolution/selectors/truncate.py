# -*- coding: utf-8 -*-

import pandas

from simmate.apps.evolution.selectors import Selector


class TruncatedSelection(Selector):
    """
    Truncated selection limits the parent selection to the top X% of individuals,
    and then within this top section, every individual has an equal chance of
    being selected.
    """

    @staticmethod
    def select(
        nselect: int,
        individuals: pandas.DataFrame,
        fitness_column: str,
        percentile: float = 0.05,
        # at min/max, make sure we can select from this number of individuals
        ntruncate_min: int = 5,
        ntruncate_max: int = 50,
        # whether we can select the same individual more than once
        allow_duplicate: bool = True,
    ) -> pandas.DataFrame:
        # truncate the population to those with energies in the lowest X%. This
        # value should be greater or equal to our minimum set above
        ntruncate = int(len(individuals) * percentile)
        if ntruncate < ntruncate_min:
            ntruncate = ntruncate_min
        if ntruncate > ntruncate_max:
            ntruncate = ntruncate_max

        # limit our potential selection to the top X% and then randomly select
        # the correct number of parents
        df_truncated = individuals.nsmallest(ntruncate, fitness_column)
        df_parents = df_truncated.sample(nselect, replace=allow_duplicate)

        # return the list of indexes to be selected
        return df_parents
