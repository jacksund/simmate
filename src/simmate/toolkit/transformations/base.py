# -*- coding: utf-8 -*-

import logging
from abc import ABC, abstractmethod


class Transformation(ABC):

    """
    This is an abstract base class (ABC) that shows you how to write your
    own Transformation class. It defines the requirements for you and raises
    errors if you forgot to define something.

    Using this abstract class, here's an example subclass that you could write
    -------------------------------------
    class SubClass(Transformation):
        io_type = 'one_to_one'
        ninput = 1
        use_multiprocessing = False
        def apply_transformation(self, structure):
            # do some transform on the input
            return new_structure
    -------------------------------------
    # example use
    t = SubClass()
    new_structure = t.apply_transformation(structure)
    -------------------------------------

    This is an updated version of pymatgen's transformation class because they
    do not support many_to_one or many_to_many:
    pymatgen.transformations.transformation_abc
    see https://pymatgen.org/pymatgen.transformations.transformation_abc.html
    """

    @property
    # @abstractmethod #!!! uncomment when I no longer assume the value
    def io_type(self):
        """
        Should I do StructureTransformation, LatticeTransformation, and
        SiteTransformation subclasses? Here, io_type could be either
        'structure', 'lattice', or 'site' as to indicate the input.
        """
        #!!! For now, I have all transformations as StructureTransformation
        #!!! so I assume io_type here. This may change in the future.
        return "structure"

    @property
    @abstractmethod
    def io_scale(self):
        """
        The input/output type for the class.
        This should be one of the following choices:
            - one_to_one
            - one_to_many
            - many_to_one
            - many_to_many # I have no examples of this yet
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def use_multiprocessing(self):
        """
        Whether or not this transformation can be done in parallel.
        Simply set to True or False.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def ninput(self):
        """
        Number of inputs required. For example, some transformations require
        two structures to be input. If one_to_* we know ninput = 1.
        """
        raise NotImplementedError

    @abstractmethod
    def apply_transformation(self):
        """
        The code that carries out the
        """
        raise NotImplementedError

    def apply_from_database_and_selector(
        self,
        selector,
        datatable,
        select_kwargs: dict = {},
        max_attempts: int = 100,
        **kwargs,  # for apply_transformation_with_validation
    ):

        logging.info(f"Creating a transformed structure with {self.__class__.__name__}")
        logging.info(f"Parent(s) will be selected using {selector.__class__.__name__}")

        # grab parent structures using the selection method
        parent_ids, parent_structures = selector.select_from_datatable(
            nselect=self.ninput,
            datatable=datatable,
            **select_kwargs,
        )

        # Until we get a new valid structure (or run out of attempts), keep trying
        # with our given source. Assume we don't have a valid structure until
        # proven otherwise
        new_structure = False
        attempt = 0
        while not new_structure and attempt <= max_attempts:
            # add an attempt
            attempt += 1

            # make a new structure
            new_structure = self.apply_transformation_with_validation(
                parent_structures,
                **kwargs,
            )

        # see if we got a structure or if we hit the max attempts and there's
        # a serious problem!
        if not new_structure:
            logging.warning(
                f"Failed to create a structure after {max_attempts} different"
                "parent combinations. Giving up."
            )
            return False

        # Otherwise we were successful
        logging.info("Creation Successful.")

        return parent_ids, new_structure

    def apply_transformation_with_validation(
        self,
        structures,  # either a structure or list of structures. Depends on ninput.
        validators=[],
        max_attempts=100,
    ):

        # Until we get a new valid structure (or run out of attempts), keep trying
        # with our given source. Assume we don't have a valid structure until
        # proven otherwise
        new_structure = False
        attempt = 0
        while not new_structure and attempt <= max_attempts:
            # add an attempt
            attempt += 1

            # make a new structure
            new_structure = self.apply_transformation(structures)

            # check to see if the structure passes all validation checks.
            if new_structure:

                for validator in validators:
                    is_valid = validator.check_structure(new_structure)

                    if not is_valid:
                        # if it is not unique, we can throw away the structure and
                        # try the loop again.
                        logging.debug(
                            "Generated structure failed validation by "
                            f"{validator.__class__.__name__}. Trying again."
                        )
                        new_structure = None

                        # one failed validation is enough to stop. There is no
                        # need to test the other validation methods.
                        break

        # see if we got a structure or if we hit the max attempts and there's
        # a serious problem!
        if not new_structure:
            logging.warning(
                "Failed to create a structure from input after "
                f"{max_attempts} attempts"
            )
            return False

        # return the structure and its parents
        return new_structure
