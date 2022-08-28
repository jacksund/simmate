# -*- coding: utf-8 -*-

from ase.ga.soft_mutation import SoftMutation as ASESoftMutation
from ase.ga.utilities import closest_distances_generator
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class SoftMutation(Transformation):
    """
    This is a wrapper around the `SoftMutation` in ase.ga
    https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py
    """

    # construct a dynamical matrix based on bond hardness and mutate site coords
    # along the softest mode
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    # This appears to be a means to order a disordered structure, which I can
    # use other pymatgen methods for:
    # from pymatgen.transformations.standard_transformations import OrderDisorderedStructureTransformation
    # from pymatgen.transformations.advanced_transformations import EnumerateStructureTransformation
    # After reading through the docs of these functions, it actually looks
    # like "disordered" refers to structures with mixed occupancy sites
    # (e.g. 50% Li / 50% Na) so... I don't think these functions will help.
    # The same goes for the reverse of these functions:
    # from pymatgen.transformations.advanced_transformations import DisorderOrderedTransformation

    # I have found that ASE has a version of this function written already
    # https://wiki.fysik.dtu.dk/ase/tutorials/ga/ga_bulk.html
    # https://gitlab.com/ase/ase/-/tree/master/ase/ga
    # from ase.ga.bulk_mutations import SoftMutation

    name = "from_ase.SoftMutation"
    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        ratio_of_covalent_radii: float = 0.1,
        bounds: list[float] = [0.5, 2.0],
        use_tags: bool = False,
        used_modes_file: str = None,
    ) -> Structure:

        # This mutation is not possible for structures that have only one site
        if structure.num_sites == 1:
            print(
                "You cannot perform a soft mutation on structures that only "
                "have one site!! You can make this a supercell and try "
                "again though."
            )
            return False

        # ----------- SETUP (consider caching as class attribute) -------------
        # the closest_distances_generator is exactly the same as an
        # element-dependent distance matrix expect ASE puts this in
        # dictionary form the function requires a list of element integers
        element_ints = [element.number for element in structure.composition]
        # the default of the ratio of covalent radii (0.1) is based on the
        # ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )
        # ---------------------------------------------------------------------

        # now make the SoftMutation mutator
        softmut = ASESoftMutation(
            blmin=element_distance_matrix,
            bounds=bounds,
            use_tags=use_tags,
            used_modes_file=used_modes_file,
        )

        # first I need to convert the structure to an ASE atoms object
        structure_ase = AseAtomsAdaptor.get_atoms(structure)

        # their code searches for a atoms.info['confid'] to check for
        # previously used modes -- it's unfortunately dependent on the entire
        # ga structure config stands for configuration, which I'm not actually
        # using. So I set this to some random value which has no effect.
        structure_ase.info.update({"confid": 0})
        # !!! I don't understand what this index represents and need to contact
        # the ase dev team

        # reset the used_modes to none
        #!!! I could also fill this if I want to try different modes until
        # I have a unique structure. The dictionary would be {0:[3,4,5...]}
        # if I want to skip modes
        softmut.used_modes = {}

        #!!! Their code suggests the use of .get_new_individual() but I think
        # .mutate() is what we'd like new_structure_ase,
        # label = self.softmut.get_new_individual([structure_ase])
        new_structure_ase = softmut.mutate(structure_ase)

        # if the mutation failed, None will be returned
        if new_structure_ase:
            # now convert back to a pymatgen object
            new_structure = AseAtomsAdaptor.get_structure(new_structure_ase)
        # this indicates the mutation failed
        else:
            new_structure = False

        return new_structure
