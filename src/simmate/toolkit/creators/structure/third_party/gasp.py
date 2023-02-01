# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator


class GaspStructure(StructureCreator):
    """
    Create structures using the GASP package.

    BUG: only reduced compositions are possible.
    This is enforced within GASP here:
    https://github.com/henniggroup/GASP-python/blob/master/gasp/general.py#L603-L605

    see source: https://github.com/henniggroup/GASP-python
    see tutorials: https://github.com/henniggroup/GASP-python/blob/master/docs/usage.md
    """

    # DEV NOTE:
    # The documentation and code organization is pretty difficult to follow for GASP,
    # so I don't include any of their options. Instead, I assume all default values
    # for a fixed composition. There's not much I can do about this until GASP fixes
    # the organization of their code and add documentation. As-is, GASP is not ment to
    # be used as a python module, which really hinders its reusability.

    def __init__(self, composition: Composition):
        try:
            from gasp.development import Constraints
            from gasp.general import CompositionSpace, IDGenerator
            from gasp.organism_creators import RandomOrganismCreator
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "You must have GASP installed to use GaspStructure. "
                "It must be installed from source: "
                "https://github.com/henniggroup/GASP-python"
            )

        # generate the inputs required for GASP to make a new structure
        # I assume all defaults for GASP right now
        self.composition_space = CompositionSpace([composition.formula])
        self.constraints = Constraints(None, self.composition_space)
        self.id_generator = IDGenerator()
        self.random_org_creator = RandomOrganismCreator(
            None,
            self.composition_space,
            self.constraints,
        )

        # this creator doesnt use sym so P1 is the only option
        self.spacegroup_options = [1]

    def create_structure(self) -> Structure:
        # sometimes gasp fails to make a structure, but let's loop it until
        # we get a valid one
        structure_gasp = False
        while not structure_gasp:
            # now make the new structure using
            #   gasp.organism_creators.RandomOrganismCreator
            structure_gasp = self.random_org_creator.create_organism(
                self.id_generator,
                self.composition_space,
                self.constraints,
                numpy.random,
            )

        # Grab the cell object from the output
        structure_gasp = structure_gasp.cell

        # convert the gasp Cell object to pymatgen Structure
        # Cell is really a child of Structure, so I'm actually
        # reducing functionality here
        structure = Structure(
            lattice=structure_gasp.lattice,
            species=structure_gasp.species,
            coords=structure_gasp.frac_coords,
        )

        return structure
