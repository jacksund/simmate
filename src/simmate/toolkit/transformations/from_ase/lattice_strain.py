# -*- coding: utf-8 -*-

from ase.ga.standardmutations import StrainMutation
from ase.ga.utilities import CellBounds, closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class LatticeStrain(Transformation):
    """
    This is a wrapper around the `StrainMutation` in ase.ga
    https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py
    """

    name = "from_ase.LatticeStrain"
    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        ratio_of_covalent_radii: float = 0.1,
    ) -> Structure:
        # ----------- SETUP (consider caching as class attribute) -------------
        # the closest_distances_generator is exactly the same as an
        # element-dependent distance matrix expect ASE puts this in dictionary
        # form the function requires a list of element integers
        element_ints = [element.number for element in structure.composition]
        # the default of the ratio of covalent radii (0.1) is based on the
        # ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice I only do angle limits for now but I
        # should introduce vector length limits
        cellbounds = CellBounds(
            bounds={
                "phi": [35, 145],
                "chi": [35, 145],
                "psi": [35, 145],
            }
        )
        #'a': [3, 50], 'b': [3, 50], 'c': [3, 50]})

        # now we can make the generator
        strain = StrainMutation(
            blmin=element_distance_matrix,  # distance cutoff matrix
            cellbounds=cellbounds,
            # stddev=0.7,
            number_of_variable_cell_vectors=3,
            # use_tags=False,
            # rng=np.random,
            # verbose=False
        )
        # ---------------------------------------------------------------------

        # first I need to convert the structures to an ASE atoms object
        structure_ase = AseAtomsAdaptor.get_atoms(structure)

        #!!! Their code suggests the use of .get_new_individual() but
        # I think .mutate() is what we'd like
        new_structure_ase = strain.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = AseAtomsAdaptor.get_structure(new_structure_ase)

        return new_structure
