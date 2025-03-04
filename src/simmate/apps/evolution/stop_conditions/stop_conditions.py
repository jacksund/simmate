# -*- coding: utf-8 -*-

import logging

from pymatgen.analysis.structure_matcher import StructureMatcher
from rich.progress import track

from simmate.toolkit import Structure


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


class BasicStopConditions:
    """
    Basic stop condition used in all searches.
    """

    def check(self, search):
        # First, see if we have at least our minimum limit for *exact* structures.
        # "Exact" refers to the nsites of the structures. We want to ensure at
        # least N structures with the input/expected number of sites have been
        # calculated.
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        count_exact = search.individuals_datatable.objects.filter(
            formula_full=search.composition,
            workflow_name=search.subworkflow_name,
            energy_per_atom__isnull=False,
        ).count()
        if count_exact < search.min_structures_exact:
            return False

        # Next, see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        if search.individuals_completed.count() > search.max_structures:
            logging.info(
                "Maximum number of completed calculations hit "
                f"(n={self.max_structures})."
            )
            return True

        # The next stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than best_survival_cutoff, then
        # we can stop the search.
        # grab the best individual for reference
        best = search.best_individual

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False

        # count the number of new individuals added AFTER the best one. If it is
        # more than best_survival_cutoff, we stop the search.
        # Note, we look at all structures that have an energy_per_atom greater
        # than 1meV/atom higher than the best structure. The +1meV ensures
        # we aren't prolonging the calculation for insignificant changes in
        # the best structure. Looking at the energy also ensures that we are
        # only counting completed calculations.
        # BUG: this filter needs to be updated to fitness_value and not
        # assume we are using energy_per_atom
        num_new_structures_since_best = search.individuals.filter(
            energy_per_atom__gt=best.energy_per_atom + search.convergence_cutoff,
            finished_at__gte=best.finished_at,
        ).count()
        if num_new_structures_since_best > search.best_survival_cutoff:
            logging.info(
                "Best individual has not changed after "
                f"{self.best_survival_cutoff} new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False


class ExpectedStructure(StopCondition):
    """
    Stops the search if the provided expected structure has been found.
    """

    def __init__(self, expected_structure: Structure):
        self.expected_structure = expected_structure

    def check(self, search):
        # !!! Here we compare individuals using pymatgen's StructureMatcher. An
        # alternative would be to use the searches validator property like we
        # do to find unique individuals in the search itself. Depending on how
        # slow the following for loop is, that may be necessary

        # get completed individuals
        individuals = search.individuals_completed.order_by("finished_at").all()
        structures = individuals.to_toolkit()

        # create instance of structure matcher
        matcher = StructureMatcher(attempt_supercell=True)

        # for each structure, check if it matches the expected structure
        for n, structure in track(list(enumerate(structures))):

            is_match = matcher.fit(self.expected_structure, structure)
            if is_match:
                # structure.to("cif", d / "match.cif")
                # We've found our structure and can immediately move on
                break

        if not is_match:
            logging.info("Search has not found groundstate yet")
            return False
        else:
            logging.info("Found groundstate!")
            return True
