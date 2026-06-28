# -*- coding: utf-8 -*-

import logging
from abc import ABC, abstractmethod

from simmate.utils import dispatch


class StructureCreator(ABC):
    def __init__(self):
        """
        This is where you store all settings for the creation and do the setup.
        For example, you would store the target composition here and/or
        specify the fixed volume to use. Many times, there are 'setup' steps
        that require a lot of overhead which you don't want to redo for each
        new creation. For example, you don't want to find all combinations
        of allowed wyckoff sites for a specific composition each time you make
        a new structure, so you would find all valid combinations here in the
        __init__ so you don't have to repeatedly find combos below in create()
        """
        pass

    @classmethod
    @property
    def name(cls):
        """
        A nice string name for the creator. By default it just returns the name
        of this class.
        """
        return cls.__name__

    @abstractmethod
    def create_structure(self, spacegroup=None):
        """
        For all different structure creators, there should be a method of
        .new_structure() that makes the new object. The main rule for this
        function is that it must return a single pymatgen structure object.
        How that structure object is created is up to each method!

        Below is some example code for how Structures are typically made. How
        the spacegroup/lattice/species/coords is determined is up to each
        methodand not shown.

        # import module (do this outside the class functions)
        from simmate.toolkit import Structure

        # run your method that makes the lattice/species/coords or uses the
        # inputs from above.
        ...

        # for new_structure method that doesnt use symmetry or wyckoff sites
        sg = 1 # this is never used but just for bookkeeping
        structure = Structure(lattice = lattice,
                              species = species,
                              coords = coords)

        # for new_structure methods that depend on symmetry and wyckoff sites
        # If you give the sites in the asym unit, they will be replicated
        # elsewhere in the unitcell using spacegroup symmetry operations.
        structure = Structure.from_spacegroup(sg = spacegroup,
                                              lattice = lattice,
                                              species = species,
                                              coords = coords)
        """
        raise NotImplementedError

    def create_many_structures(self, n, spacegroup=None):
        """
        This is a convience function to create many structures in parallel.
        In most cases, you don't want to redefine this function.
        It is assumed that calling create_structure() repeatedly is the
        fastest method to make new structures, so that is the function
        parallelized. In some cases (such as the USPEX creator), there is a
        lot of overhead with a single call to create_structure(), so it may
        make more sense to have the main structure creation code in this
        function. See the USPEXStructure Creator class for an example of this.
        """
        # USING DISPATCH TO PARALLELIZE
        results = dispatch(
            [spacegroup] * n,
            self.create_structure,
            parallel=True,
        )
        return results

    def update_data(self):
        """
        TO-DO
        This is a function to update settings. For example, I could use this
        to update the self.lattice_creator method to a more accurate volume.
        I can run machine learning code here before updating too.
        """
        pass

    def create_structure_with_validation(self, validators=[], max_attempts=100):
        # While some structure creators go through validation while they are being
        # created (e.g. a site-distances check), there may be higher-level
        # validations that need to be done. I may need to rethink and refactor
        # the distinction between the two though.

        # Until we get a new valid structure (or run out of attempts), keep trying
        # with our given source. Assume we don't have a valid structure until
        # proven otherwise
        logging.info(f"Creating new structure with {self.name}")
        new_structure = False
        attempt = 0
        while not new_structure and attempt <= max_attempts:
            # add an attempt
            attempt += 1
            # make a new structure
            new_structure = self.create_structure()

            # check to see if the structure passes all validation checks.
            if new_structure:
                for validator in validators:
                    is_valid = validator.check_structure(new_structure)

                    if not is_valid:
                        # if it is not unique, we can throw away the structure and
                        # try the loop again.
                        logging.info(
                            "Generated structure is failed validation by "
                            f"{validator.name}. Trying again."
                        )
                        new_structure = None

                        # one failed validation is enough to stop. There is no
                        # need to test the other validation methods.
                        break

        # see if we got a structure or if we hit the max attempts and there's
        # a serious problem!
        if not new_structure:
            logging.warning(
                "Failed to create a structure! Consider changing your settings or"
                " contact our team for help."
            )
            return False, False

        # Otherwise we were successful
        logging.info("Creation Successful.")

        # return the structure and its parents
        return new_structure
