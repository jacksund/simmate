# -*- coding: utf-8 -*-

from numpy.random import choice

from simmate.toolkit.creators.structure.base import StructureCreator


class PyXtalStructure(StructureCreator):

    # see docs: https://pyxtal.readthedocs.io/en/latest/index.html

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object,
        volume_factor=1.0,
        default_lattice=None,
        tolerance_matrix=None,  # options unique to PyXtal's random_crystal
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
    ):

        #!!! this is inside the init because not all users will have this installed!
        try:
            from pyxtal import pyxtal
        except ModuleNotFoundError:
            #!!! I should raise an error in the future
            raise Exception("You must have PyXtal installed to use PyXtalStructure!!")

        # save the module for reference below
        self.pyxtal = pyxtal()

        # save the composition information in the format that PyXtal wants ['Ca', 'N']
        self.species = [element.symbol for element in composition.elements]
        # save the number of Ions in the format that PyXtal wants [3,2]
        self.numIons = [
            int(composition[element.symbol]) for element in composition.elements
        ]
        # save the volume factor to be used later
        self.volume_factor = volume_factor
        # if the user supplied a lattice, it should be a 3x3 matrix -- NOT a pymatgen lattice object
        #!!! should I add a check that this is a matrix here?
        self.default_lattice = default_lattice
        #!!! TO-DO: I need to allow the user to specify the tolerance matrix
        if tolerance_matrix:
            print(
                "Simmate's wrapper for PyXtal does not currently support setting "
                "the tolerance matrix for PyXtal's random_crystal(). If you want this "
                "option added, please contact the Simmate developers."
            )

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]
        # Note, there's no easy way to see which spacegroups are compatible with
        # our composition, so this list is updated as attempts fail in the
        # create_structure method.

    def create_structure(self, spacegroup=None):

        # If a spacegroup is not specified, grab a random one from our options.
        # The requested_spacegroup let's us know below if the method wanted a
        # given spacegroup -- which tells us whether or not we should raise an
        # error if the spacegroup is incompatible with our composition
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)
            requested_spacegroup = False
        else:
            requested_spacegroup = True

        from pyxtal.msg import Comp_CompatibilityError

        try:
            # now make the new structure using PyXtal's crystal.random_crystal function
            # NOTE: all of these options are set in the init except for the spacegroup
            # No structure is returned. Instead they just attach it to the pyxtal object
            self.pyxtal.from_random(
                group=int(
                    spacegroup
                ),  # !!! why do I need int() here? This should already work without it...
                species=self.species,
                numIons=self.numIons,
                factor=self.volume_factor,
                lattice=self.default_lattice,
            )
            # tm=<pyxtal.crystal.Tol_matrix object> # not supported right now!
        except Comp_CompatibilityError as exception:
            # if the user wanted this spacegroup, raise the error
            if requested_spacegroup:
                raise exception
            # otherwise remove the spacegroup from our allowed list
            self.spacegroup_options.remove(spacegroup)
            # And retry! Note: recursion is a shortcut here, but shouldn't be an issue
            self.create_structure()

        # note that we have a PyXtal structure object, not a PyMatGen one!
        # The PyXtal structure has a *.valid feature that lets you know if structure creation was a success
        # so we will check that
        if self.pyxtal.valid:
            # if it is valid, we want the PyMatGen structure object, which is at *.struct
            return self.pyxtal.to_toolkit()
        else:
            # if it is not valid, the structure creation failed
            return False
