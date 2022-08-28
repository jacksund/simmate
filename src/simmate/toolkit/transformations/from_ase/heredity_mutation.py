# -*- coding: utf-8 -*-

import numpy
from ase import Atoms
from ase.ga.cutandsplicepairing import CutAndSplicePairing
from ase.ga.utilities import CellBounds, closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class Heredity(Transformation):
    """
    This is a wrapper around the `CutAndSplicePairing` in ase.ga
    https://gitlab.com/ase/ase/-/blob/master/ase/ga/cutandsplicepairing.py
    """

    # TODO: I need to figure out how to implement more than two structures
    # might be useful for a pymatgen rewrite:
    # pymatgen.transformations.advanced_transformations.SlabTransformation

    name = "from_ase.Heredity"
    io_scale = "many_to_one"
    ninput = 2
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structures: list[Structure],
        ratio_of_covalent_radii: float = 0.1,
    ) -> Structure:
        #!!! takes two structures!

        # ----------- SETUP (consider caching as class attribute) -------------
        #!!! I assume 3D structure for now. I could do things like
        # pbc=[1,1,0] for 2D in the future though
        slab = Atoms(pbc=True)

        # the closest_distances_generator is exactly the same as an
        # element-dependent distance matrix expect ASE puts this in dictionary
        # form the function requires a list of element integers
        element_ints = [element.number for element in structures[0].composition]
        # the default of the ratio of covalent radii (0.1) is based on the
        # ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice. I only do angle limits for now but
        # I should introduce vector length limits
        cellbounds = CellBounds(
            bounds={
                "phi": [35, 145],
                "chi": [35, 145],
                "psi": [35, 145],
            }
        )
        #'a': [3, 50], 'b': [3, 50], 'c': [3, 50]})
        # ---------------------------------------------------------------------

        # split the structures into independent variables
        # copy because we may edit these into supercells below
        structure1, structure2 = [s.copy() for s in structures]

        # ASE requires the structures to be the same size but doesn't try
        # them to scale themselves. If we have two structures have the same
        # composition, we can just make supercells to make them the same size.
        if structure1.num_sites != structure2.num_sites:
            # get the least common multiple
            lcm = numpy.lcm(structure1.num_sites, structure2.num_sites)

            # scale each structure to that lcm. We don't care about the shape,
            # just that the sites come out the
            structure1.make_supercell([int(lcm / structure1.num_sites), 1, 1])
            structure2.make_supercell([int(lcm / structure2.num_sites), 1, 1])
            # BUG: This can give a structure with too large of a composition

        # if the structures each only have one site, the mutation will fail
        if structure1.num_sites == 1:
            print(
                "You cannot perform a heredity mutation on structures that "
                "only have one site!! You can make this a supercell and "
                "try again though."
            )
            return False
        # TODO: should I should make the supercell for them?

        # now we can make the generator
        casp = CutAndSplicePairing(
            # indicated dimensionality
            slab=slab,
            # number of atoms to optimize. I set this to all
            n_top=int(structure1.composition.num_atoms),
            # distance cutoff matrix
            blmin=element_distance_matrix,
            #!!! I understand this as number of unique vectors. Is that right?
            number_of_variable_cell_vectors=3,
            # p1=1, # probablitiy of shifting
            # p2=0.05, # probablitiy of shifting
            # minimum fraction of atoms that a parent must contribute.
            # None is one atom.
            # minfrac=None,
            cellbounds=cellbounds,
            # test_dist_to_slab=True,
            # use_tags=False,
            # rng=np.random,verbose=False
        )

        # first I need to convert the structures to an ASE atoms object
        structure1_ase = AseAtomsAdaptor.get_atoms(structure1)
        structure2_ase = AseAtomsAdaptor.get_atoms(structure2)

        #!!! Their code suggests the use of .get_new_individual() but I think
        # .cross() is what we'd like
        new_structure_ase = casp.cross(structure1_ase, structure2_ase)

        # if the mutation fails, None is returned
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = AseAtomsAdaptor.get_structure(new_structure_ase)

        return new_structure
