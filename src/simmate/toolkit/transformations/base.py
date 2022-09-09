# -*- coding: utf-8 -*-

import logging

from simmate.toolkit import Structure


class Transformation:
    """
    Transformations (aka "mutations") alter an input structure (or structures)
    in some way. For now we assume all transformations are for toolkit
    `Structure` objects

    Different transformation can take a different number of structures as inputs
    and also potentially return more than one structure. Therefore, pay close
    attention to setting `io_scale` and `ninput`

    ## Example use

    When writing a custom transformation class, you can use the following example:

    ``` python
    class SubClass(Transformation):
        io_scale = 'one_to_one'
        ninput = 1
        allow_parallel = True
        def apply_transformation(self, structure):
            # do some transform on the input
            return new_structure

    # example use
    t = SubClass()
    new_structure = t.apply_transformation(structure)
    ```

    This is a refactored version of pymatgen's
    [Transformation](https://pymatgen.org/pymatgen.transformations.transformation_abc.html)
    class because they do not support many_to_one or many_to_many
    (see pymatgen.transformations.transformation_abc)
    """

    io_type: str = "structure"
    """
    Should I do StructureTransformation, LatticeTransformation, and
    SiteTransformation subclasses? Here, io_type could be either
    'structure', 'lattice', or 'site' as to indicate the input.
    """
    #!!! For now, I have all transformations as StructureTransformation
    #!!! so I assume io_type here. This may change in the future.

    allow_parallel: bool = False
    """
    Whether or not this transformation can be done in parallel.
    
    In pymatgen, this parameter is named `use_multiprocessing`
    """

    @property
    def io_scale(self) -> str:
        """
        The input/output type for the class.
        This should be one of the following choices:
            - one_to_one
            - one_to_many
            - many_to_one
            - many_to_many # I have no examples of this yet
        """
        raise NotImplementedError(
            "Make sure you set a `io_scale` for your Transformation class"
        )

    @property
    def ninput(self):
        """
        Number of inputs required. For example, some transformations require
        two structures to be input. If one_to_* we know ninput = 1.
        """
        raise NotImplementedError(
            "Make sure you set `ninput` for your Transformation class"
        )

    def apply_transformation(self, structure: Structure) -> Structure:
        """
        This method carries out the transformation. The typing shown above
        is an example of a `one_to_one` transformation that accepts a
        single structure and returns a single one.
        """
        raise NotImplementedError(
            "Make sure you define a new `apply_transformation` for "
            "your Transformation class"
        )

    @classmethod
    @property
    def name(cls):
        """
        A nice string name for the transformation. By default it just returns
        the name of this class.
        """
        return cls.__name__

    def apply_from_database_and_selector(
        self,
        selector,
        datatable,
        select_kwargs: dict = {},
        max_attempts: int = 100,
        **kwargs,  # for apply_transformation_with_validation
    ):

        logging.info(f"Creating a transformed structure with {self.name}")
        logging.info(f"Parent(s) will be selected using {selector.name}")

        # grab parent structures using the selection method
        parent_ids, parent_structures = selector.select_from_datatable(
            nselect=self.ninput,
            datatable=datatable,
            **select_kwargs,
        )

        logging.info(f"Selected parents: {parent_ids}")

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
                "Failed to create a structure from input after "
                f"{max_attempts} attempts"
            )
            return False

        # return the structure and its parents
        return new_structure
