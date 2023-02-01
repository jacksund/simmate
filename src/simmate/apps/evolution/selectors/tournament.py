# -*- coding: utf-8 -*-

import pandas

from simmate.apps.evolution.selectors import Selector


class TournamentSelection(Selector):
    """
    Tournament selection selects N parents randomly and then choses the single
    best of these those randomly selected. If multiple individuals are requested,
    a separate tournament is used to select each.
    """

    @staticmethod
    def select(
        nselect: int,
        individuals: pandas.DataFrame,
        fitness_column: str,
        # The percent of individuals participating in each tournament
        tournament_size: float = 0.20,
        tournament_min: int = 3,
    ) -> pandas.DataFrame:
        # We want the tournament size to be based on the total number of
        # inidividuals available.
        ntournament = int(len(individuals) * tournament_size)
        if ntournament < tournament_min:
            ntournament = tournament_min

        # Run the series of tournaments and select the winner from each
        tournament_winners = []
        for n in range(nselect):
            df_tourn = individuals.sample(ntournament, replace=False)
            winner = df_tourn.nsmallest(1, fitness_column).iloc[0]
            tournament_winners.append(winner)

        # take the winning series and convert back to a pandas dataframe
        df_parents = pandas.DataFrame(tournament_winners)
        df_parents = df_parents.reset_index(drop=True)  # in case of duplicates

        return df_parents
