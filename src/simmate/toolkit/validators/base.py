# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod

from dask.diagnostics import ProgressBar
from dask import bag


class Validator(ABC):
    @abstractmethod
    def check_structure(self, structure):
        # User needs to define this function where one structure is input.
        # The output should be a True or False value that indicates whether
        # or not the structure passed the check.
        raise NotImplementedError

    def check_many_structures(self, structures, progressbar=True, mode="threads"):
        # USING DASK TO PARALLELIZE
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
