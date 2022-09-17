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

    @classmethod
    def from_dynamic(cls, validator):
        
        # already a validator object
        if isinstance(validator, cls):
            return validator
        
        # dictionary of validator_name + validator_kwargs
        elif isinstance(validator, dict) and "validator_name" in validator.keys():
            pass

            
        # from an evolutionary search object
        
        # from an evolutionary search database table entry 
        #   (database_table = "FixedComposition")
        
        # unknown
        
        pass

    @staticmethod
    def from_evolutionary_search(database_obj):
        # Initialize the fingerprint database
        # For this we need to grab all previously calculated structures of this
        # compositon too pass in too.
        
        from simmate.toolkit import Composition
        from simmate.toolkit.validators import fingerprint as validator_module

        validator_class = getattr(validator_module, database_obj.validator_name)

        fingerprint_validator = validator_class(
            composition=Composition(database_obj.composition),
            structure_pool=database_obj.individuals,
            **database_obj.validator_kwargs,
        )
        logging.info("Done generating fingerprints.")

        # BUG: should we only do structures that were successfully calculated?
        # If not, there's a chance a structure fails because of something like a
        # crashed slurm job, but it's never submitted again...
        # OPTIMIZE: should we only do final structures? Or should I include input
        # structures and even all ionic steps as well...?
        return fingerprint_validator
