# -*- coding: utf-8 -*-

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
