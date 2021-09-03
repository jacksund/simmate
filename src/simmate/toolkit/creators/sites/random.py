# -*- coding: utf-8 -*-

from pymatdisc.core.creators.vector import UniformlyDistributedVectors


#!! NOTE: I should make a copy of this that is RandomSymSites, where I limit the
# random sites generated to the asym unit of the specified spacegroup
class RandomSites:
    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        coords_generation_method=UniformlyDistributedVectors,
        coords_gen_options=dict(),
    ):

        # save the composition for reference
        self.composition = composition

        # establish the coords generator
        self.coords_generator = coords_generation_method(**coords_gen_options)

    def new_sites(self):

        # make an empty list to store all the fractional coordinates
        coords_list = []  # regular list.append is faster than numpy.append
        # as well as an empty list for the species
        species_list = []

        # let's go through each element in composition one at a time
        for element in self.composition:
            # element is a key to composition that returns nsites
            # for example, composition['Ca'] = 2 for Ca2N
            nsites = int(self.composition[element])
            for site in range(nsites):
                # use the generator to create random fractional coordinates
                coords = self.coords_generator.new_vector()
                # append the coords and species to our output lists
                coords_list.append(coords)
                species_list.append(element)

        # maybe make these into pymatgen Site objects? I don't see any advantage to Site object,
        # because we will later need PeriodicSite objects and there's no direct conversion method
        return species_list, coords_list
