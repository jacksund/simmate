# -*- coding: utf-8 -*-

from ase import Atoms
from ase.ga.startgenerator import StartGenerator
from ase.ga.utilities import CellBounds, closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator


class AseStructure(StructureCreator):
    """
    Creates structures using ASE's start-generator

    see source: https://gitlab.com/ase/ase/-/blob/master/ase/ga/startgenerator.py
    see tutorials: https://wiki.fysik.dtu.dk/ase/ase/ga/ga.html#module-ase.ga
    """

    def __init__(
        self,
        composition: Composition,
        ratio_of_covalent_radii: int = 0.5,
    ):
        # I assume 3D structure for now. I could do things like pbc=[1,1,0]
        # for 2D in the future though
        slab = Atoms(pbc=True)

        # the blocks input is just a list of building blocks and how many to
        # include of each for example, Ca2N would have [('Ca', 2), ('N', 1)].
        # let's convert the pymatgen composition object to this format - other
        # formats are allowed too
        blocks = [
            (element.symbol, int(composition[element])) for element in composition
        ]

        # the closest_distances_generator is exactly the same as an
        # element-dependent distance matrix. ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.5) is based on the
        # ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice
        # I only do angle limits for now because I try to set the volume below
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
            # !!! I understand this as number of unique vectors. Is that right?
            number_of_variable_cell_vectors=3,
            # box_to_place_in=None, # use the entire unitcell
            box_volume=volume_guess,  # target this volume when making the lattice
            cellbounds=cellbounds,
            # test_dist_to_slab=True, # ensure distances arent too close
            # test_too_far=True, # ensure no atom is isolated
            # rng=np.random
        )

    def create_structure(self) -> Structure:
        # now make the new structure using ase,ga.startgenerator
        # NOTE: all of these options are set in the init except for spacegroup
        structure_ase = self.ase.get_new_candidate(maxiter=1000)

        # if creation fails, None is returned
        if not structure_ase:
            return False

        # convert the ase Atoms object to pymatgen Structure
        structure = AseAtomsAdaptor.get_structure(structure_ase)

        return structure
