# -*- coding: utf-8 -*-

from dask import bag
from dask.diagnostics import ProgressBar


class Validator:
    @classmethod
    @property
    def name(cls):
        """
        A nice string name for the validator. By default it just returns the name
        of this class by default.
        """
        return cls.__name__

    def check_structure(self, structure):
        # User needs to define this function where one structure is input.
        # The output should be a True or False value that indicates whether
        # or not the structure passed the check.
        raise NotImplementedError(
            "make sure you add a custom 'check_structure' method to your Validator"
        )

    def check_many_structures(self, structures, progressbar=True, mode="threads"):
        # REFACTOR: switch to the get_dask_client utility here.

        # using dask to parallelize
        structures_bag = bag.from_sequence(structures)
        validation_bag = structures_bag.map(self.check_structure)

        # Based on whether the user wants a progress bar or not, decide how
        # the compute() command is called.
        if progressbar:
            with ProgressBar():
                checks = validation_bag.compute(scheduler=mode)
        else:
            checks = validation_bag.compute(scheduler=mode)

        return checks
