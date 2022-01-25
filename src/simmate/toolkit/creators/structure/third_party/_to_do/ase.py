# -*- coding: utf-8 -*-


class ASEStructure:

    # see source: https://gitlab.com/ase/ase/-/blob/master/ase/ga/startgenerator.py
    # see tutorials: https://wiki.fysik.dtu.dk/ase/ase/ga/ga.html#module-ase.ga

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        ratio_of_covalent_radii=0.5,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.startgenerator import StartGenerator
        from ase.ga.utilities import closest_distances_generator

        # the slab variable is there to specify dimensionality. The code really just uses the pbc setting
        #!!! I need to doublecheck this
        from ase import Atoms

        slab = Atoms(
            pbc=True
        )  #!!! I assume 3D structure for now. I could do things like pbc=[1,1,0] for 2D in the future though

        # the blocks input is just a list of building blocks and how many to include of each
        # for example, Ca2N would have [('Ca', 2), ('N', 1)].
        # let's convert the pymatgen composition object to this format - other formats are allowed too (see docs)
        blocks = [
            (element.symbol, int(composition[element])) for element in composition
        ]

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.5) is based on the ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice
        # I only do angle limits for now because I try to set the volume below
        from ase.ga.utilities import CellBounds

        cellbounds = CellBounds(
            bounds={
                "phi": [60, 120],
                "chi": [60, 120],
                "psi": [60, 120],
            }
        )
        #'a': [3, 50], 'b': [3, 50], 'c': [3, 50]})

        # predict volume
        volume_guess = composition.volume_estimate()

        self.ase = StartGenerator(
            slab=slab,
            blocks=blocks,
            blmin=element_distance_matrix,
            number_of_variable_cell_vectors=3,  #!!! I understand this as number of unique vectors. Is that right?
            # box_to_place_in=None, # use the entire unitcell
            box_volume=volume_guess,  # target this volume when making the lattice
            # splits=None, # increases translational sym (good for large atom counts - forces symmetry)
            cellbounds=cellbounds,
            # test_dist_to_slab=True, # ensure distances arent too close
            # test_too_far=True, # ensure no atom is isolated (distance is >2x the min cutoff)
            # rng=np.random
        )

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: ASE.ga does not allow for specification of atomic sites and your "
                "specification here will be overwritten."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While ASE.ga allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: ASE.ga does not use symmetry to generate their structures "
                "and specifying this has no effect."
            )

        # now make the new structure using ase,ga.startgenerator
        # NOTE: all of these options are set in the init except for the spacegroup
        structure_ase = self.ase.get_new_candidate(
            maxiter=1000
        )  #!!! I should set a limit on the iterations here

        # if creation fails, None is returned
        if not structure_ase:
            return False

        # convert the ase Atoms object to pymatgen Structure
        from pymatgen.io.ase import AseAtomsAdaptor

        structure = AseAtomsAdaptor.get_structure(structure_ase)

        return structure
