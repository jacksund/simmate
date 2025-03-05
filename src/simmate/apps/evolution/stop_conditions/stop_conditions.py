# -*- coding: utf-8 -*-

import logging

from pymatgen.analysis.structure_matcher import StructureMatcher
from rich.progress import track

from simmate.toolkit import Composition, Structure


class StopCondition:
    def __init__(
        self,
        search,
    ):
        # Inheriting classes can add any required kwargs here. These will then
        # need to be defined in the input settings. The only required kwarg is
        # the search.
        pass

    def check(self):
        # The check method should take no arguments and instead use any instance
        # variables defined in the __init__ function
        # The StopCondition can run any analysis on the Search object WITHOUT
        # making any changes to it. Then you should return True if the
        # stopping condition(s) has been met and False if the calculation should
        # continue.
        pass


class BasicStopConditions:
    """
    Basic stop condition used in all searches.
    """

    def __init__(
        self,
        search,
        max_structures: int = None,
        min_structures_exact: int = None,
        convergence_cutoff: float = 0.001,
        best_survival_cutoff: int = None,
    ):
        # Convergence criteria and stop conditions can be set based on the
        # number of atoms in the composition. Here we try to set reasonable criteria
        # for these if a user-input was not given. Note we are using max(..., N)
        # to set an absolute minimum for these.
        n = Composition(search.composition).num_atoms
        min_structures_exact = min_structures_exact or max([int(30 * n), 100])
        max_structures = max_structures or max([int(n * 250 + n**2.75), 1500])
        best_survival_cutoff = best_survival_cutoff or max([int(30 * n + n**2), 100])
        # update the search fields related to these settings
        search.update_from_fields(
            min_structures_exact=min_structures_exact,
            max_structures=max_structures,
            best_survival_cutoff=best_survival_cutoff,
        )
        # add instance variables
        self.search = search
        self.max_structures = max_structures
        self.min_structures_exact = min_structures_exact
        self.convergence_cutoff = convergence_cutoff
        self.best_survival_cutoff = best_survival_cutoff

    def check(self):
        # First, see if we have at least our minimum limit for *exact* structures.
        # "Exact" refers to the nsites of the structures. We want to ensure at
        # least N structures with the input/expected number of sites have been
        # calculated.
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        count_exact = self.search.individuals_datatable.objects.filter(
            formula_full=self.search.composition,
            workflow_name=self.search.subworkflow_name,
            energy_per_atom__isnull=False,
        ).count()
        if count_exact < self.min_structures_exact:
            return False

        # Next, see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        if self.search.individuals_completed.count() > self.max_structures:
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
        best = self.search.best_individual

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
        num_new_structures_since_best = self.search.individuals.filter(
            energy_per_atom__gt=best.energy_per_atom + self.convergence_cutoff,
            finished_at__gte=best.finished_at,
        ).count()
        if num_new_structures_since_best > self.best_survival_cutoff:
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

    def __init__(
        self,
        search,
        expected_structure: Structure,
    ):
        # get expected structure and make sure it is a pymatgen Structure object
        self.expected_structure = Structure.from_dynamic(expected_structure)
        self.search = search

    def check(self):
        # !!! Here we compare individuals using pymatgen's StructureMatcher. An
        # alternative would be to use the searches validator property like we
        # do to find unique individuals in the search itself. Depending on how
        # slow the following for loop is, that may be necessary

        expected_structure = self.expected_structure
        breakpoint()
        # get completed individuals since the last check. If this is our first
        # check we instead use the start time.
        if self.search.last_check_timestamp is None:
            last_time = self.search.started_at
        else:
            last_time = self.search.last_check_timestamp
        individuals = self.search.individuals_completed.filter(
            finished_at__gte=last_time
        ).all()
        # make sure we have some individuals to compare to. If not, we haven't
        # finished any structures yet and immedieately return False
        if len(individuals) == 0:
            return False

        structures = individuals.to_toolkit()

        # create instance of structure matcher
        matcher = StructureMatcher(attempt_supercell=True)

        # for each structure, check if it matches the expected structure
        for n, structure in track(list(enumerate(structures))):

            is_match = matcher.fit(expected_structure, structure)
            if is_match:
                # structure.to("cif", d / "match.cif")
                # We've found our structure and can immediately move on
                break

        if not is_match:
            logging.info("Search has not found expected structure yet")
            return False
        else:
            logging.info("Found expected structure!")
            return True
