# -*- coding: utf-8 -*-

from ase.ga.standardmutations import PermutationMutation
from ase.ga.utilities import closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class AtomicPermutation(Transformation):
    """
    This is a wrapper around the `PermutationMutation` in ase.ga
    https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py
    """

    name = "from_ase.AtomicPermutation"
    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        ratio_of_covalent_radii: float = 0.1,
    ) -> Structure:
        # This mutation is not possible for structures that have only one element
        if len(structure.composition.elements) == 1:
            print(
                "You cannot perform an atomic permutation on a structure that"
                " only has one element type!!"
            )
            return False

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

        perm = PermutationMutation(
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all
            probability=0.33,  # probability an atom is permutated
            # test_dist_to_slab=True,
            # use_tags=False,
            blmin=element_distance_matrix,  # distance cutoff matrix
            # rng=np.random,
            # verbose=False
        )

        #!!! Their code suggests the use of .get_new_individual() but I think
        # .mutate() is what we'd like
        new_structure_ase = perm.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = AseAtomsAdaptor.get_structure(new_structure_ase)

        return new_structure
