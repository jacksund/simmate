# -*- coding: utf-8 -*-

from ase.ga.standardmutations import RattleMutation
from ase.ga.utilities import closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class CoordinatePerturbation(Transformation):
    """
    This is a wrapper around the `RattleMutation` in ase.ga
    https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py
    """

    name = "from_ase.CoordinatePerturbation"
    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        perturb_strength: float = 0.8,
        ratio_of_covalent_radii: float = 0.1,
    ) -> Structure:
        # ----------- SETUP (consider caching as class attribute) -------------
        # The closest_distances_generator is exactly the same as an
        # element-dependent distance matrix, except ASE puts this in dictionary
        # form. The function requires a list of element integers
        element_ints = [element.number for element in structure.composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE
        # tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )
        # ---------------------------------------------------------------------

        # first I need to convert the structures to an ASE atoms object
        structure_ase = AseAtomsAdaptor.get_atoms(structure)

        # now we can make the generator
        rattle = RattleMutation(
            blmin=element_distance_matrix,  # distance cutoff matrix
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all,
            rattle_strength=perturb_strength,  # strength of rattling
            rattle_prop=1,  # propobility that atom is rattled
            test_dist_to_slab=True,
            # rng=np.random  # TODO: consider changing to normal dist
        )

        #!!! Their code suggests the use of .get_new_individual() but I think
        # .mutate() is what we'd like
        new_structure_ase = rattle.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = AseAtomsAdaptor.get_structure(new_structure_ase)

        return new_structure
