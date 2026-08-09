# -*- coding: utf-8 -*-

from simmate.utils import dispatch


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

    def check_many_structures(
        self,
        structures,
        parallel: bool | str = True,
    ):
        checks = dispatch(
            structures,
            self.check_structure,
            parallel=parallel,
        )
        return checks
