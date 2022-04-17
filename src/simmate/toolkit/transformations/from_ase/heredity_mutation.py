# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit.transformations.base import Transformation


#!!! I need to figure out how to implement more than two structures


class Heredity(Transformation):

    # known as CutAndSplicePairing in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/cutandsplicepairing.py

    # might be useful for a pymatgen rewrite:
    # pymatgen.transformations.advanced_transformations.SlabTransformation

    io_scale = "many_to_one"
    ninput = 2
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.utilities import closest_distances_generator

        # the slab variable is there to specify dimensionality. The code really just uses the pbc setting
        #!!! I need to doublecheck this
        from ase import Atoms

        self.slab = Atoms(
            pbc=True
        )  #!!! I assume 3D structure for now. I could do things like pbc=[1,1,0] for 2D in the future though

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        self.element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice
        # I only do angle limits for now but I should introduce vector length limits
        from ase.ga.utilities import CellBounds

        self.cellbounds = CellBounds(
            bounds={
                "phi": [35, 145],
                "chi": [35, 145],
                "psi": [35, 145],
            }
        )
        #'a': [3, 50], 'b': [3, 50], 'c': [3, 50]})

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structures):  #!!! takes two structures!

        # split the structures into independent variables
        structure1, structure2 = [
            s.copy() for s in structures
        ]  # copy because we may edit these into supercells below

        ### CHECK FOR BUGS

        # ASE requires the structures to be the same size but doesn't try
        # them to scale themselves. If we have two structures have the same
        # composition, we can just make supercells to make them the same size.
        if structure1.num_sites != structure2.num_sites:
            # get the least common multiple
            lcm = numpy.lcm(structure1.num_sites, structure2.num_sites)

            # scale each structure to that lcm
            # we don't care about the shape, just that the sites come out the same size
            #!!! THIS CAN GIVE A STRUCTURE WITH TOO LARGE OF A COMPOSITION!! NEED TO FIX THIS -----------------------------------------------------------------------
            structure1.make_supercell([int(lcm / structure1.num_sites), 1, 1])
            structure2.make_supercell([int(lcm / structure2.num_sites), 1, 1])

        # if the structures each only have one site, the mutation will fail
        if structure1.num_sites == 1:
            # print('You cannot perform a heredity mutation on structures that only have one site!! You can make this a supercell and try again though.')
            return False

        ### RUN

        # !!! This was moved below because composition isn't known right away -- the number of sites varies
        # now we can make the generator
        from ase.ga.cutandsplicepairing import CutAndSplicePairing

        self.casp = CutAndSplicePairing(
            slab=self.slab,  # indicated dimensionality
            n_top=int(
                structure1.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all
            blmin=self.element_distance_matrix,  # distance cutoff matrix
            number_of_variable_cell_vectors=3,  #!!! I understand this as number of unique vectors. Is that right?
            # p1=1, # probablitiy of shifting
            # p2=0.05, # probablitiy of shifting
            # minfrac=None, # minimum fraction of atoms that a parent must contribute. None is one atom.
            cellbounds=self.cellbounds,
            # test_dist_to_slab=True,
            # use_tags=False,
            # rng=np.random,verbose=False
        )

        # first I need to convert the structures to an ASE atoms object
        structure1_ase = self.adaptor.get_atoms(structure1)
        structure2_ase = self.adaptor.get_atoms(structure2)

        #!!! Their code suggests the use of .get_new_individual() but I think .cross() is what we'd like
        new_structure_ase = self.casp.cross(structure1_ase, structure2_ase)

        # if the mutation fails, None is returned
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure
