# -*- coding: utf-8 -*-

##############################################################################

from numpy.random import choice

from pymatgen.core.lattice import Lattice

from simmate.toolkit.creators.vector import (
    UniformlyDistributedVectors,
    NormallyDistributedVectors,
)

##############################################################################

# Generates a random lattice without symmetry
# this is the same as RandomSymLattice when spacegroup is assumed to be 1
class RandomLattice:
    def __init__(
        self,
        vector_generation_method=NormallyDistributedVectors,
        vector_gen_options=dict(),
        angle_generation_method=UniformlyDistributedVectors,
        angle_gen_options=dict(min_value=60, max_value=120),
    ):

        # establish the vector generation method and use the specified options
        self.vector_generator = vector_generation_method(**vector_gen_options)

        # establish the vector generation method and use the specified options
        self.angle_generator = angle_generation_method(**angle_gen_options)

    def new_lattice(self):

        # generate an (a,b,c) vector to pull lattice vectors from
        a, b, c = self.vector_generator.new_vector()

        # generate an (alpha,beta,gamme) vector to pull lattice angles from
        alpha, beta, gamma = self.angle_generator.new_vector()

        # take the inputs of vectors=(a,b,c) and angles=(alpha,beta,gamma) and create a pymatgen lattice object
        lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)

        return lattice


##############################################################################

# Generates a random lattice with symmetry
class RandomSymLattice:
    def __init__(
        self,
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
        vector_generation_method=NormallyDistributedVectors,
        vector_gen_options=dict(),
        angle_generation_method=UniformlyDistributedVectors,
        angle_gen_options=dict(min_value=60, max_value=120),
    ):

        # sg_include = list of spacegroups that we are interested in. Default is all 230 spacegroups
        # sg_exclude = list of spacegroups that we should explicitly ignore

        # establish the vector generation method and use the specified options
        self.vector_generator = vector_generation_method(**vector_gen_options)

        # establish the vector generation method and use the specified options
        self.angle_generator = angle_generation_method(**angle_gen_options)

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

    def new_lattice(self, spacegroup=None):

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # generate an (a,b,c) vector to pull lattice vectors from
        a, b, c = self.vector_generator.new_vector()

        # generate an (alpha,beta,gamme) vector to pull lattice angles from
        alpha, beta, gamma = self.angle_generator.new_vector()

        # Now generate the lattice using the spacegroup indicidated
        if spacegroup <= 2:  # triclinic
            # SPECIAL CASE b/c pymatgen does not have this function
            # but because (a != b != c) and (alpha != beta != gamma)
            # take the inputs of vectors=(a,b,c) and angles=(alpha,beta,gamma) and create a pymatgen lattice object
            lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
        elif spacegroup <= 15:  # monoclinic
            lattice = Lattice.monoclinic(a, b, c, beta)
        elif spacegroup <= 74:  # orthorhombic
            lattice = Lattice.orthorhombic(a, b, c)
        elif spacegroup <= 142:  # tetragonal
            lattice = Lattice.tetragonal(a, c)
        elif spacegroup <= 167:  # trigonal
            lattice = Lattice.hexagonal(a, c)
            # Note: I have all lattices in range(143,168) to be hexagonal
            # the spacegroups 146,148,155,160,161,166,167 can optionally be rhombohedral though
            # lattice = Lattice.rhombohedral(a,alpha)
        elif spacegroup <= 194:  # hexagonal
            lattice = Lattice.hexagonal(a, c)
        elif spacegroup <= 230:
            lattice = Lattice.cubic(a)

        # we need to know which spacegroup was used in addition to the result lattice
        # maybe I can add an option to 'returnlatticeonly=True' if I don't want this as a dict
        return lattice


##############################################################################


class RSLFixedVolume(RandomSymLattice):

    # identical to RandomSymLattice, except the lattice is scaled to a fixed volume at the end

    #!!! currently, this takes roughly 3x as long as the RandomSymLattice to run (180us vs 55.3us averages for new_lattice)
    #!!! this time increase is primarily in the .scale() function (when I comment out the check loop - I get a 154us average)

    #!!! this is fixed volume of the conventional cells! So some spacegroups may run into issues with this.
    #!!! I need a 'smart' FixedVolume that scales based on...
    # composition (total atoms and their type)
    # spacegroup (conventional vs primitive size)

    def __init__(self, volume, **kwargs):
        # run the same parent init
        super().__init__(**kwargs)

        # now do the extra code
        # which is just save the volume here
        self.volume = volume

    def new_lattice(self, spacegroup=None):
        # run the same parent new_lattice, which returns a lattice
        lattice = super().new_lattice(spacegroup)

        # now scale the lattice to the specified volume
        lattice = lattice.scale(self.volume)

        # in scaling, we might have broken the conditions of min/max_vectors
        # I check this and if it fails, I scrap the lattice and try making a new one via recursion
        check = True  # assume valid until proven otherwise
        for vector in [lattice.a, lattice.b, lattice.c]:
            if vector < self.vector_generator.min_value:
                check = False
                break
            elif vector > self.vector_generator.max_value:
                check = False
                break
        if not check:
            # this is a recursion call that will be hit repeatedly until a valid lattice is found
            #!!! this will throw a recursion error if the volume and min/max_vectors are unreasonable
            lattice = self.new_lattice(spacegroup)

        return lattice


##############################################################################

from simmate.toolkit.symmetry.wyckoff import loadWyckoffData

#!!! EASY SPEED/MEMORY IMPROVEMENTS CAN BE MADE HERE (ON INIT)
class RSLSmartVolume:
    def __init__(
        self,
        composition,
        volume=None,
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
        vector_generation_method=NormallyDistributedVectors,
        vector_gen_options=dict(),
        angle_generation_method=UniformlyDistributedVectors,
        angle_gen_options=dict(min_value=60, max_value=120),
    ):

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

        # if the user didn't specify a volume, we should predict our own
        if not volume:
            # grab the base predicted volume which is based on the composition
            # note this represents the volume of the primitive cell!!! Conventional cells may be larger
            #!!! this assumes user wants ionic radius estimation
            volume = composition.volume_estimate()

        # find the respective volume for each spacegroup's conventional unit cell
        # to do this, we need to know the ratio between MultiplicityPrimitive and MultiplicityConventiional for a spacegroup
        #!!! currently this is stored in wyckoffdata.csv, but I should consider putting it in a separate file for speed
        data = loadWyckoffData()
        self.volumes = {}  # keys are spacegroup
        self.vector_generators = {}  # keys are spacegroup
        for spacegroup in self.spacegroup_options:
            # grab the portion of the table for spacegroup and make it into a numpy array
            sg_data = data.query("SpaceGroup == @spacegroup").values
            # final the ratio between the primitive and conventional unitcells for this structure
            # this is the ratio between the 2nd and 3rd columns (indicies 1 and 2), which are MultiplicityConventional & MultiplicityPrimitive
            # I grab the first row, which is the first wyckoff site -- it makes no difference which one I grab
            ratio = sg_data[0][1] / sg_data[0][2]
            # the volume of the conventional cell for this spacegroup is the primitive times this ratio
            self.volumes.update({spacegroup: volume * ratio})

            # now we want to make the vector_generator for this spacegroup
            #!!! I'm not sure users can pass custom parameters this deep and if they will work. I need to test for this
            #!!! I assume NormallyDistributedVectors is used here... will give errors if that's not the case
            vgen = vector_generation_method(
                min_value=min(
                    composition.radii_estimate()
                ),  # smallest radius of any ion #!!! move outside for loop for speed! #!!! this assumes user wants ionic radius estimation
                center=(ratio * volume) ** (1 / 3),  # shoot for cubic vectors
                max_value=(ratio * volume)
                ** 0.8,  # don't allow for vectors too be crazy different #!!! need to test if 0.8 is a good value here
                standdev=((ratio * volume) ** (1 / 3))
                * 0.15,  # larger volumes have more flexibility in their vector lengths
            )  #!!! **vector_gen_options not used... need to fix
            self.vector_generators.update({spacegroup: vgen})

        # establish the vector generation method and use the specified options
        # Unlike the vector_generators, we can use the same generator here for all spacegroups
        self.angle_generator = angle_generation_method(**angle_gen_options)

    def new_lattice(self, spacegroup=None):

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # For our target spacegroup, grab the target volume and vector_generator
        volume = self.volumes[spacegroup]
        vector_generator = self.vector_generators[spacegroup]

        # run the same parent new_lattice, which returns a lattice
        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # generate an (a,b,c) vector to pull lattice vectors from
        a, b, c = vector_generator.new_vector()

        # generate an (alpha,beta,gamma) vector to pull lattice angles from
        alpha, beta, gamma = self.angle_generator.new_vector()

        # Now generate the lattice using the spacegroup indicidated
        if spacegroup <= 2:  # triclinic
            # SPECIAL CASE b/c pymatgen does not have this function
            # but because (a != b != c) and (alpha != beta != gamma)
            # take the inputs of vectors=(a,b,c) and angles=(alpha,beta,gamma) and create a pymatgen lattice object
            lattice = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
        elif spacegroup <= 15:  # monoclinic
            lattice = Lattice.monoclinic(a, b, c, beta)
        elif spacegroup <= 74:  # orthorhombic
            lattice = Lattice.orthorhombic(a, b, c)
        elif spacegroup <= 142:  # tetragonal
            lattice = Lattice.tetragonal(a, c)
        elif spacegroup <= 167:  # trigonal
            lattice = Lattice.hexagonal(a, c)
            # Note: I have all lattices in range(143,168) to be hexagonal
            # the spacegroups 146,148,155,160,161,166,167 can optionally be rhombohedral though
            # lattice = Lattice.rhombohedral(a,alpha)
        elif spacegroup <= 194:  # hexagonal
            lattice = Lattice.hexagonal(a, c)
        elif spacegroup <= 230:
            lattice = Lattice.cubic(a)

        #!!! This section makes the code take more than 3x longer to run. Should
        #!!! I allow a more flexible volume? More flexible volume could also slow structure creation (bc smaller volumes are allowed)
        # now scale the lattice to the specified volume
        lattice = lattice.scale(volume)
        # in scaling, we might have broken the conditions of min/max_vectors
        # I check this and if it fails, I scrap the lattice and try making a new one via recursion
        check = True  # assume valid until proven otherwise
        for vector in [lattice.a, lattice.b, lattice.c]:
            if vector < vector_generator.min_value:
                check = False
                break
            elif vector > vector_generator.max_value:
                check = False
                break
        if not check:
            # this is a recursion call that will be hit repeatedly until a valid lattice is found
            #!!! this will throw a recursion error if the volume and min/max_vectors are unreasonable
            #!!! I need to rewrite this function where it's a while loop instead of a recursion call
            lattice = self.new_lattice(spacegroup)

        # we need to know which spacegroup was used in addition to the result lattice
        # maybe I can add an option to 'returnlatticeonly=True' if I don't want this as a dict
        return lattice
