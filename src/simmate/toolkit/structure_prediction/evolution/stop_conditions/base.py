# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------

"""
Feel free to write your own StopCondition! It should follow the format shown here.

-Jack
"""


class StopCondition:
    def __init__(
        self,
    ):
        # add any unchanging variables or settings here
        pass

    def check(self, search):
        # The select method should take in one argument:
        # search = this is the main Search object seen in search.py
        # The StopCondition can run any analysis on the Search object WITHOUT
        # making any changes to it. Then you should return True if the
        # stopping condition(s) has been met and False if the calculation should
        # continue.
        pass


# -----------------------------------------------------------------------------


class BasicStopConditions:
    def __init__(self, max_structures=300, energy_limit=-999, same_min_structures=50):
        self.max_structures = max_structures
        self.energy_limit = energy_limit
        self.same_min_structures = same_min_structures

    def check(self, search):

        # Note, a single condition met is enough to stop the search (returns True)

        # start by looking at the total number of structures that completed their analysis
        if search.njobs_completed >= self.max_structures:
            print("\nMax structures hit. Stopping Search")
            return True

        # grab the completed energies and the lowest energy for reference
        energies = [e for e in search.fitnesses if e]  # remove None types
        if not energies:  # this will happen if the no structures have completed yet
            return False
        min_energy = min(energies)

        # look at the structure energies and see what the lowest is
        if min_energy <= self.energy_limit:
            print("\nEnergy limit hit. Stopping Search")
            return True

        # look how long the minimum structure has been there #!!! ERROR IN LOGIC
        # min_index = energies.index(min_energy)
        # if len(energies) - min_index >= self.same_min_structures:
        #     print('\nMin-structure reign limit hit. Stopping Search')
        #     return True

        # If no conditions above are met, return False to continue the search
        return False


# -----------------------------------------------------------------------------
