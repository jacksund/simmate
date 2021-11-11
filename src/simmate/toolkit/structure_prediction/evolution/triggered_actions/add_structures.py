# -*- coding: utf-8 -*-


class AddStructures:
    def __init__(
        self,
        n_pending_limit,
        n_add_structures,
    ):

        self.n_pending_limit = n_pending_limit

        # Number of structures to create if the pending_limit is hit
        self.n_add_structures = n_add_structures

    def check(self, search):  #!!! can I move 'search' to the init?

        # if no structures have completed yet, we don't want to add any new structure with this trigger
        if search.njobs_completed == 0:
            return False

        # See if the number of jobs pending has dropped below the limit
        if search.njobs_pending <= self.n_pending_limit:
            return True
        else:
            return False

    def action(self, search):

        print("Making new structures...")

        # we want n total structures so we are going to loop this number of times
        for n in range(self.n_add_structures):
            # make a new sample
            search.new_sample()
