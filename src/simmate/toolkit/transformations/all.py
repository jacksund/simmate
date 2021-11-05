# -*- coding: utf-8 -*-

import numpy
from numpy.random import randint, choice

from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.analysis.elasticity.strain import Strain, convert_strain_to_deformation
from pymatgen.transformations.standard_transformations import (
    PerturbStructureTransformation,
)

from simmate.toolkit.transformations.base import Transformation
from simmate.toolkit.creators.vector import UniformlyDistributedVectors

##############################################################################


class AtomicPermutation(Transformation):

    # Two atoms of different types are exchanged a variable number of times
    # See: https://uspex-team.org/static/file/JChemPhys-USPEX-2006.pdf

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    #!!! should I add an option for distribution of exchange number? Potentially use creation.vector objects?
    # USPEX states that they do this - and select from a normal distribution
    def __init__(self, min_exchanges=1, max_exchanges=5):

        # save inputs for reference
        self.min_exchanges = min_exchanges
        self.max_exchanges = max_exchanges

        #!!! when doing multiple exchanges, I do not check to see if an exchange has been done before - I can change this though
        # Therefore one exchange could undo another and we could be back where we started
        # There are also scenarios where all sites are equivalent and atomic permutation cannot create a new structure
        # An example of this is NaCl, where an exchange still yields an identical structure
        # This leaves a chance that we end up with an identical structure to what we started with.
        # Therefore, I must hava a structurematcher object that I use to ensure we have a new structure
        # We try making a new structure X number of times (see max_attempts above) and if we can't, we failed to mutate the structure!
        self.structure_matcher = (
            StructureMatcher()
        )  #!!! I should lower the tolerances here!

    def apply_transformation(self, structure, max_attempts=100):

        # grab a list of the elements
        #!!! consider moving this to init to save time at the cost of more in memory
        elements = structure.composition.elements

        # This mutation is not possible for structures that have only one element
        if len(elements) == 1:
            print(
                "You cannot perform an atomic permutation on structure that only has one element type!!"
            )
            return False
        #!!! add another elif for when all sites are equivalent and atomic permutation cannot create a new structure

        for attempt in range(max_attempts):  # I could alternatively do a while loop

            # make a deepcopy of the structure so that we aren't modifying it inplace
            # this also allows us to compare the new structure to the original
            # placing this at the top of the loop also resets the structure for us each time
            new_structure = structure.copy()

            # grab a random integer within the exchange range (min/max) defined above
            nexchanges = randint(low=self.min_exchanges, high=self.max_exchanges)

            # perform an exchange of two random atom types X number of times
            for n in range(nexchanges):
                # grab two elements of different types
                element1, element2 = choice(elements, size=2)

                # select a random index of element1 and element2
                index1 = choice(new_structure.indices_from_symbol(element1.symbol))
                index2 = choice(new_structure.indices_from_symbol(element2.symbol))

                # now exchange the species type of those two sites
                new_structure.replace(index1, element2)
                new_structure.replace(index2, element1)

            # see if the new structure is different from the original!
            # check will be True if the new structure is the same as the original
            check = self.structure_matcher.fit(structure, new_structure)
            if not check:
                # we successfully make a new structure!
                return new_structure
            # else continue

        # if we make it this far, then we hit our max_attempts limit without making a new structure
        # therefore, we failed the mutation
        print("Failed to make a new structure that is different from the original")
        return False


##############################################################################


class LatticeStrain(Transformation):

    #!!! should I mutate atomic sites too? USPEX is unclear if they do this in addition to lattice strain
    #!!! if I decide to do this, look at CoordinateMutation class below

    # strain is applied to the lattice and then the lattice is scaled back to target volume
    # https://uspex-team.org/static/file/CPC-USPEX-2006.pdf

    # It looks like structure.apply_strain() is simply scaling each lattice vector and not exactly what we'd like
    # Instead, I found pymatgen.analysis.elasticity.strain module
    # https://pymatgen.org/pymatgen.analysis.elasticity.strain.html
    # Here, my understanding is that a strain matrix is not equivalent to a deformation matrix
    # therefore, I will create a Strain object, then convert it Deformation object, then apply it to the structure

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(self, fixed_volume):

        # after straining the lattice, we need to scale it to a fixed volume
        self.fixed_volume = fixed_volume

        # following along with USPEX paper, we need to first establish boundries for the symmetric strain matrix
        # when generating components for this matrix, they randomly select values between -1 and 1 in a guassian distribution
        self.component_generator = UniformlyDistributedVectors(
            min_value=-1, max_value=1
        )

    def apply_transformation(self, structure, max_attempts=100):

        # first we need 6 strain matrix components
        components = self.component_generator.new_vector(size=6)

        # next we need to assemble the strain matrix using these components
        #!!! is there a better way to do this? I'm just using equation (3) in the USPEX paper
        strain_matrix = [
            [1 + components[0], components[5] / 2, components[4] / 2],
            [components[5] / 2, 1 + components[1], components[3] / 2],
            [components[4] / 2, components[3] / 2, 1 + components[2]],
        ]

        # now let's switch to pymatgen functionality

        # first make the Strain object
        strain = Strain(strain_matrix)

        # now convert it to a deformation object
        #!!! do I want the shape to be 'upper' or 'symmetric'??
        deformation = convert_strain_to_deformation(strain, shape="symmetric")

        # deform the structure
        new_structure = deformation.apply_to_structure(structure)

        # scale the lattice volume back to a fixed value
        new_structure.scale_lattice(self.fixed_volume)

        return new_structure


##############################################################################


class CoordinatePerturbation(Transformation):

    # random perturbation of sites was removed from USPEX because primarily made more defective + lower energy structures
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    # note, the function Structure.pertrub displaces each site at an equal distance
    # this function on the other hand displaces at a variable distance selected from a guassian distribution between min/mix
    # this transformation is almost guaranteed to give a structure with P1 symmetry

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(self, min_displace=0, max_displace=1):  #!!! whats a good displacement?

        self.perturb_object = PerturbStructureTransformation(min_displace, max_displace)

    def apply_transformation(self, structure):

        new_structure = self.perturb_object.apply_transformation(structure)

        return new_structure


##############################################################################


class CoordinateOrderedPerturbation(Transformation):

    # known as "coordinate mutation" in USPEX
    # site locations are mutated where sites with lower order have higher preference for mutation
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf
    # ""Coordinate mutation was found [2] to be ineffective, because “blind” displacement of the
    # atoms is much more likely to decrease the quality of a structure than to increase it.""
    #!!! because of the quote above, the coordinate displacement is order-dependent

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
    ):
        pass

    def apply_transformation(self, structure, max_attempts=100):
        return


##############################################################################


class SoftMutationASE(Transformation):

    # construct a dynamical matrix based on bond hardness and mutate site coords along the softest mode
    # https://uspex-team.org/static/file/USPEX-LargeComplexSystems-2010.pdf

    # This appears to be a means to order a disordered structure, which I can use other pymatgen methods for
    # from pymatgen.transformations.standard_transformations import OrderDisorderedStructureTransformation
    # from pymatgen.transformations.advanced_transformations import EnumerateStructureTransformation
    # After reading through the docs of these functions, it actually looks like "disordered" refers to structures with mixed occupancy sites (e.g. 50% Li / 50% Na)
    # so... I don't think these functions will help
    # the same goes for the reverse of these functions:
    # from pymatgen.transformations.advanced_transformations import DisorderOrderedTransformation

    # I have found that ASE has a version of this function written already
    # https://wiki.fysik.dtu.dk/ase/tutorials/ga/ga_bulk.html
    # https://gitlab.com/ase/ase/-/tree/master/ase/ga
    # from ase.ga.bulk_mutations import SoftMutation

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
        bounds=[0.5, 2.0],
        use_tags=False,
        used_modes_file=None,
    ):  #!!! add all SoftMutation options or use **kwargs?

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.soft_mutation import SoftMutation
        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # now make the SoftMutation mutator
        self.softmut = SoftMutation(
            blmin=element_distance_matrix,
            bounds=bounds,
            use_tags=use_tags,
            used_modes_file=used_modes_file,
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        ### CHECK FOR BUGS

        # This mutation is not possible for structures that have only one site
        if structure.num_sites == 1:
            # print('You cannot perform a soft mutation on structures that only have one site!! You can make this a supercell and try again though.')
            return False

        ### RUN

        # first I need to convert the structure to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # their code searches for a atoms.info['confid'] to check for previously used modes -- it's unfortunately dependent on the entire ga structure
        # config stands for configuration, which I'm not actually using. So I set this to some random value which has no effect.
        structure_ase.info.update(
            {"confid": 0}
        )  #!!! I don't understand what this index represents and need to contact the dev

        # reset the used_modes to none
        #!!! I could also fill this if I want to try different modes until I have a unique structure
        #!!! the dictionary would be {0:[3,4,5...]} if I want to skip modes
        self.softmut.used_modes = {}

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        # new_structure_ase, label = self.softmut.get_new_individual([structure_ase])
        new_structure_ase = self.softmut.mutate(structure_ase)

        # if the mutation failed, None will be returned
        if new_structure_ase:
            # now convert back to a pymatgen object
            new_structure = self.adaptor.get_structure(new_structure_ase)
        # this indicates the mutation failed
        #!!! should I retry?
        else:
            new_structure = False

        return new_structure


##############################################################################

#!!! I need to figure out how to implement more than two structures
class HeredityASE(Transformation):

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
        from ase.ga.cutandsplicepairing import CutAndSplicePairing
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


##############################################################################


class CoordinatePerturbationASE(Transformation):

    # known as RattleMutation in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        self.element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        # first I need to convert the structures to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # now we can make the generator
        from ase.ga.standardmutations import RattleMutation

        self.rattle = RattleMutation(
            blmin=self.element_distance_matrix,  # distance cutoff matrix
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all,
            # rattle_strength=0.8, # strength of rattling
            # rattle_prop=0.4, # propobility that atom is rattled
            # test_dist_to_slab=True,
            # use_tags=False,
            # verbose=False,
            # rng=np.random
        )

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        new_structure_ase = self.rattle.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure


##############################################################################


class AtomicPermutationASE(Transformation):

    # known as PermutationMutation in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        self.element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        ### CHECK FOR BUGS

        # This mutation is not possible for structures that have only one element
        if len(structure.composition.elements) == 1:
            print(
                "You cannot perform an atomic permutation on structure that only has one element type!!"
            )
            return False

        ### RUN

        # first I need to convert the structures to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # now we can make the generator
        from ase.ga.standardmutations import PermutationMutation

        perm = PermutationMutation(
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all
            probability=0.33,  # probability an atom is permutated
            # test_dist_to_slab=True,
            # use_tags=False,
            blmin=self.element_distance_matrix,  # distance cutoff matrix
            # rng=np.random,
            # verbose=False
        )

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        new_structure_ase = perm.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure


##############################################################################


class MirrorMutationASE(Transformation):

    # known as MirrorMutation in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors

        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        self.element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        ### CHECK FOR BUGS

        #!!! TO-DO. In many cases, you can perform this operation and simply
        # get back the original structure. I should check and make sure
        # that I'm actually returning a new structure!

        ### RUN

        # first I need to convert the structures to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # now we can make the generator
        from ase.ga.standardmutations import MirrorMutation

        mirror = MirrorMutation(
            blmin=self.element_distance_matrix,  # distance cutoff matrix
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all
            # reflect=False, #!!! need to look into this more
            # rng=np.random,
            # verbose=False
        )

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        new_structure_ase = mirror.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure


##############################################################################


class LatticeStrainASE(Transformation):

    # known as StrainMutation in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors
        from ase.ga.standardmutations import StrainMutation
        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # boundry limits on the lattice
        # I only do angle limits for now but I should introduce vector length limits
        from ase.ga.utilities import CellBounds

        cellbounds = CellBounds(
            bounds={
                "phi": [35, 145],
                "chi": [35, 145],
                "psi": [35, 145],
            }
        )
        #'a': [3, 50], 'b': [3, 50], 'c': [3, 50]})

        # now we can make the generator
        self.strain = StrainMutation(
            blmin=element_distance_matrix,  # distance cutoff matrix
            cellbounds=cellbounds,
            # stddev=0.7,
            number_of_variable_cell_vectors=3,
            # use_tags=False,
            # rng=np.random,
            # verbose=False
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        # first I need to convert the structures to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        new_structure_ase = self.strain.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure


##############################################################################


class RotationalMutationASE(Transformation):

    # known as RotationalMutation in ase.ga
    # https://gitlab.com/ase/ase/-/blob/master/ase/ga/standardmutations.py

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    def __init__(
        self,
        composition,
        ratio_of_covalent_radii=0.1,
    ):

        # we can assume the user has ASE installed because it is a dependency of PyMatgen
        #!!! it looks like the ase.ga module is actively changing so version may introduce errors

        from ase.ga.utilities import closest_distances_generator

        # the closest_distances_generator is exactly the same as an element-dependent distance matrix
        # expect ASE puts this in dictionary form
        # the function requires a list of element integers
        element_ints = [element.number for element in composition]
        # the default of the ratio of covalent radii (0.1) is based on the ASE tutorial of this function
        self.element_distance_matrix = closest_distances_generator(
            element_ints, ratio_of_covalent_radii
        )

        # we also need to convert pymatgen Structures to ase Atoms below
        #!!! is it faster and more memory efficient to import below?
        from pymatgen.io.ase import AseAtomsAdaptor

        self.adaptor = AseAtomsAdaptor

    def apply_transformation(self, structure):

        ### CHECK FOR BUGS

        #!!! TO-DO. In many cases, you can perform this operation and simply
        # get back the original structure. I should check and make sure
        # that I'm actually returning a new structure!

        ### RUN

        # first I need to convert the structures to an ASE atoms object
        structure_ase = self.adaptor.get_atoms(structure)

        # now we can make the generator
        from ase.ga.standardmutations import RotationalMutation

        rotate = RotationalMutation(
            blmin=self.element_distance_matrix,  # distance cutoff matrix
            n_top=int(
                structure.composition.num_atoms
            ),  # number of atoms to optimize. I set this to all
            # fraction=0.33,
            # tags=None,
            # min_angle=1.57,
            # test_dist_to_slab=True,
            # rng=np.random,
            # verbose=False
        )

        #!!! Their code suggests the use of .get_new_individual() but I think .mutate() is what we'd like
        new_structure_ase = rotate.mutate(structure_ase)

        # if the mutation fails, None is return
        if not new_structure_ase:
            return False

        # if it was successful, we have a new Atoms object
        # now convert back to a pymatgen object
        new_structure = self.adaptor.get_structure(new_structure_ase)

        return new_structure


##############################################################################
