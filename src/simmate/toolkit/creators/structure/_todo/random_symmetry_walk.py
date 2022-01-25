# -*- coding: utf-8 -*-

import pandas as pd
from numpy.random import choice, shuffle
import itertools

from simmate.toolkit import Structure, Composition

from pymatdisc.core.symmetry.wyckoff import loadWyckoffData
from pymatdisc.core.creators.vector import UniformlyDistributedVectors
from pymatdisc.core.creators.sites import (
    asymmetric_unit_boundries,
)  #!!! this will move to pymatdisc.symmetry in the future
from pymatdisc.core.creators.lattice import (
    RSLSmartVolume,
)  #!!! naming likely to change on this class too
from pymatdisc.core.estimate import distance_matrix

##############################################################################


class StructureCreator:
    def __init__(
        self,
        composition,
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
        max_total_attempt=1e6,
        max_large_mult_attempt=400,
        max_dist_attempt=100,
    ):

        # save general input
        self.max_large_mult_attempt = max_large_mult_attempt
        self.max_dist_attempt = max_dist_attempt
        self.max_total_attempt = max_total_attempt
        self.composition = composition
        self.spacegroup_exclude = spacegroup_exclude
        self.spacegroup_include = spacegroup_include

        # list of spacegroups that can be used
        self.space_group_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]
        # assign lattice gen method
        self.lattice_generator = RSLSmartVolume(composition)
        # assign udv to spacegroups
        self.vector_creator = {}
        for sg in self.space_group_options:
            aub = asymmetric_unit_boundries(sg)
            udv = UniformlyDistributedVectors(extra_conditions=aub)
            self.vector_creator[sg] = udv
        # load wyckoff data
        self.wy_data = loadWyckoffData()

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # shuffle compostion order
        elements = [e for e in self.composition]
        shuffle(elements)
        comp_dict = {}

        for i in elements:
            comp_dict[i] = self.composition[i]
        # create new ordered composition from dictionary
        new_composition = Composition.from_dict(comp_dict)
        # create cutoff matrix for composition
        cutoff_matrix = distance_matrix(new_composition, radius_method="atomic")

        if not spacegroup:
            spacegroup = choice(self.space_group_options)

        udv = self.vector_creator[spacegroup]

        if not lattice:
            struct_lattice = self.lattice_generator.new_lattice(spacegroup)

        spacegroup_data = self.wy_data.query("SpaceGroup==@spacegroup")
        sg_data = spacegroup_data.values

        # list to hold every wy_site added
        master_wy_list = []
        species_list = []
        coords_list = []
        # test_struct = Structure(struct_lattice, species_list, coords_list)

        for element in new_composition:
            # create list to hold wy sites for element
            element_sites = []
            # list to hold multiplicity values
            mults = []
            # while loop check
            master_check = False
            large_mult_attempt = 0
            total_attempt_count = 0
            while not master_check:  # while not check and (attempts <= ...)

                #!!! add an attempt
                total_attempt_count += 1
                if total_attempt_count == self.max_total_attempt:
                    self.space_group_options.remove(spacegroup)
                    return False

                # grab a random wy site
                wy_site = sg_data[choice(len(sg_data))]
                wy_letter = wy_site[3]  # 3 = index of letter
                wy_coord = wy_site[5]  # 5 = index of coordinate
                wy_mult = wy_site[1]  # 1 = site multiplicity

                # check site availability
                avail_check = True
                if wy_site[6] == 1.0:  # 6 = site availability
                    # see if this wy_letter has been used by the current element yet
                    if wy_letter in element_sites:
                        avail_check = False
                    # see if any other elements used the wy_site already
                    for species in master_wy_list:
                        if wy_letter in species:
                            avail_check = False
                            break  # no need to look at any other species
                    if avail_check == False:
                        continue  # restart while loop
                # else: all other sites are assumed to have infinite availability

                # check multiplicity
                mult_check = False
                mults_total = sum(mults) + wy_mult
                if mults_total == self.composition[element]:
                    element_sites.append(wy_letter)
                    mults.append(wy_site[1])  # 1 = multiplicity of wy_site
                    mult_check = True  #!!! is this the correct placement? Even before distance check? -Jack
                elif mults_total < self.composition[element]:
                    mults.append(wy_site[1])
                    element_sites.append(wy_letter)
                elif mults_total > self.composition[element]:
                    large_mult_attempt += 1
                    if (
                        large_mult_attempt == self.max_large_mult_attempt
                        and element_sites
                    ):
                        element_sites.pop()
                        mults.pop()
                    continue  # restart while loop

                # check if wy_letter can be successfully added to structure
                dist_check = False
                dist_attempt = 0

                while not dist_check:

                    # add an attempt
                    dist_attempt += 1

                    # see if we have maxed out our number of attempts
                    if dist_attempt == self.max_dist_attempt:
                        break  # this breaks the while loop with dist_check = False

                    # make the new vector coords
                    # note that these value will be used to eval the wy_site coords
                    x, y, z = udv.new_vector()
                    new_coord = eval(wy_coord)
                    specie = str(element)
                    coords_list.append(new_coord)
                    species_list.append(specie)
                    # test_struct.append(specie, new_coord)

                    dist_check = True  # assume its good until proven otherwise
                    fsg_test_struct = Structure.from_spacegroup(
                        spacegroup, struct_lattice, species_list, coords_list
                    )
                    #!!! speed improvements to be made here...?
                    # check distances in full unit cell to see if its too close to another site
                    fsg_dm = fsg_test_struct.distance_matrix

                    for x, specie1 in enumerate(new_composition):
                        specie1_indicies = fsg_test_struct.indices_from_symbol(
                            specie1.symbol
                        )
                        for y, specie2 in enumerate(new_composition):
                            specie2_indicies = fsg_test_struct.indices_from_symbol(
                                specie2.symbol
                            )
                            dist_cutoff = cutoff_matrix[x][y]
                            combos = itertools.product(
                                specie1_indicies, specie2_indicies
                            )
                            for s1, s2 in combos:
                                if s1 == s2:
                                    continue
                                distance = fsg_dm[s1][s2]
                                if distance < dist_cutoff:
                                    dist_check = False

                    # see if the distance check passed or not
                    if not dist_check:
                        # if not, remove the site and try again
                        # test_struct.pop() # do i have to pop from strucutre??
                        species_list.pop()
                        coords_list.pop()
                        continue

                # see if all checks (mult, avail, dist) above passed
                if dist_check:
                    # mult_check signifies whether total nsites has been reached so it is not necessarily true at this point
                    # still have to assign a coordinate to wy site even if mult_check isn't true
                    if mult_check:
                        master_check = (
                            True  # if mult_check is true flg end of main while loop
                        )
                    # if mult_check is false, another wy site will be assigned to the element
                    # if mult_check is true, program will move onto next element
                    continue
                else:
                    # if maxed out of attempts restart main while loop to pick different wy site
                    if element_sites:
                        element_sites.pop()
                        mults.pop()
                    # we want to restart the while loop
                    # since master_check was never changed, we dont need to reset it
                    # master_check=False

            # append wy letters for element to master list of wy letters
            master_wy_list.append(element_sites)

        return fsg_test_struct
