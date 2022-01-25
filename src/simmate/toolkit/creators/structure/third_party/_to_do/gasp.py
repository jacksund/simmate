# -*- coding: utf-8 -*-

from simmate.toolkit import Structure


class GASPStructure:

    # see source: https://github.com/henniggroup/GASP-python
    # see tutorials: https://github.com/henniggroup/GASP-python/blob/master/docs/usage.md

    #!!! The documentation and code organization is pretty difficult to follow for GASP,
    #!!! so I don't include any of their options. Instead, I assume all default values
    #!!! for a fixed composition. There's not much I can do about this until GASP fixes
    #!!! the organization of their code and add documentation. As-is, GASP is not ment to
    #!!! be used as a python module, which really hinders its reusability.

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
    ):

        #!!! this is inside the init because not all users will have this installed!
        try:
            from gasp.general import CompositionSpace, IDGenerator
            from gasp.development import Constraints
            from gasp.organism_creators import RandomOrganismCreator
        except ModuleNotFoundError:
            #!!! I should raise an error in the future
            print("You must have GASP installed to use GASPStructure!!")
            return  # exit the function as the script will fail later on otherwise

        # generate the inputs required for GASP to make a new structure
        #!!! I assume all defaults for GASP right now
        self.composition_space = CompositionSpace([composition.formula])
        self.constraints = Constraints(
            None, self.composition_space
        )  #!!! TO-DO add distance matrix (I currently do this through generator)
        self.id_generator = IDGenerator()
        self.random_org_creator = RandomOrganismCreator(
            None, self.composition_space, self.constraints
        )

        #!!! GASP uses a random module as an input here... This should be fixed
        from numpy import random

        self.random = random

        # this creator doesnt use sym so P1 is the only option
        self.spacegroup_options = [1]

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: GASP does not allow for specification of atomic sites and your "
                "specification here will be overwritten."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While GASP allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: GASP does not use symmetry to generate their structures "
                "and specifying this has no effect."
            )

        # sometimes gasp fails to make a structure, but let's loop it until we get a valid one
        structure_gasp = False
        while not structure_gasp:
            # now make the new structure using gasp.organism_creators.RandomOrganismCreator
            #!!! currently this prints a message, which I can't mute
            structure_gasp = self.random_org_creator.create_organism(
                self.id_generator, self.composition_space, self.constraints, self.random
            )
        # # the output will be None if the creation failed
        # if not structure_gasp:
        #     # creation failed, so return false
        #     return False

        # Grab the cell object from the output
        structure_gasp = structure_gasp.cell

        # convert the gasp Cell object to pymatgen Structure
        # Cell is really a child of Structure, so I'm actually reducing functionality here
        structure = Structure(
            lattice=structure_gasp.lattice,
            species=structure_gasp.species,
            coords=structure_gasp.frac_coords,
        )

        return structure
