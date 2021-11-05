# -*- coding: utf-8 -*-

from numpy.random import randint, choice

from tqdm import tqdm

from simmate.toolkit.symmetry.wyckoff import (
    loadAsymmetricUnitData,
    loadWyckoffData,
    findValidWyckoffCombos,
)
from simmate.toolkit.creators.vector import UniformlyDistributedVectors


class RandomWySites:
    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
        coords_generation_method=UniformlyDistributedVectors,
        coords_gen_options=dict(),  # asymmetric_unit_boundries is include in extra_conditions automatically
    ):

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

        # save the composition for reference
        self.composition = composition

        # the stoichiometry of the composition will be used repeatedly below
        # it's easier to save that here for reference too
        # convert the composition to a stoichiometry list
        # for example, Mg4Si4O12 composition will have stoich=[4,4,12]
        stoichiometry = [int(composition[element]) for element in composition]
        self.stoichiometry = stoichiometry

        # Find valid wyckoff combinatons for all spacegroups and stoichiometry
        # I want the combinations and info to be stored as a dictionary of {spacegroup:combos/info} entries
        self.wy_groupinfo = {}
        self.wy_groupcombos = {}
        # some spacegroups will be incompatible with the given composition -- keep a list of these
        self.spacegroups_invalid = []
        #!!! NOTE: This code takes a long time to run in some cases, so I want to do it up front
        # because this takes time, I print a warning and then use tqdm to track progress
        message = "Generating Wyckoff combinations for every spacegroup: "
        for spacegroup in tqdm(self.spacegroup_options, desc=message):
            sg_combo_data = findValidWyckoffCombos(stoichiometry, spacegroup)
            # If the spacegroup + stoich combination has no valid combinations, the generator will not work
            if not sg_combo_data["ValidCombinations"]:
                self.spacegroups_invalid.append(spacegroup)
                # no need to save these results so skip to the next spacegroup
                continue
            # splitting up this dictionary becuase we reference each a lot
            # and append the results to respective dictionaries
            self.wy_groupinfo.update({spacegroup: sg_combo_data["WyckoffGroups"]})
            self.wy_groupcombos.update({spacegroup: sg_combo_data["ValidCombinations"]})
        # we need to take the spacegroups that are invalid and update the spacegroup_options with it.
        # we still save the self.spacegroups_invalid for the user to see #!!! consider removing self.spacegroups_invalid though
        self.spacegroup_options = [
            sg for sg in self.spacegroup_options if sg not in self.spacegroups_invalid
        ]

        # make all generators for each spacegroup
        # the generators are different for each spacegroup because each has a different asym unit
        #!!! NOTE: options set in coords_gen_options will apply to all spacegroups
        # I want the generators to be stored as a dictionary of {spacegroup:generator} entries
        self.coords_generators = {}
        for spacegroup in self.spacegroup_options:
            # grab a copy of the user inputs for reference
            # we will manipulate final_options for each spacegroup for use in the generator
            final_options = coords_gen_options.copy()
            # If the spacegroup was found to have no valid wyckoff combinations, there is no need for a generator
            if spacegroup in self.spacegroups_invalid:
                # skip to next spacegroup
                continue
            # establish the coords generator with asymmetric_unit_boundries
            # this process is a little more complicated because we require that the asymmetric_unit_boundries be included in extra_conditions
            asym_bounds = asymmetric_unit_boundries(spacegroup)
            # if any extra_conditions were provided by the user, we want to combine them with the asym conditions
            if "extra_conditions" in coords_gen_options.keys():
                all_bounds = coords_gen_options["extra_conditions"] + asym_bounds
                final_options.update({"extra_conditions": all_bounds})
            # otherwise, the asym_bounds are the only boundry conditions for the coordinates
            else:
                final_options.update({"extra_conditions": asym_bounds})
            # now that we have the coords_gen_options updated, we can make the generator
            coords_generator = coords_generation_method(**final_options)
            # add this generator to the results
            self.coords_generators.update({spacegroup: coords_generator})

        # below, I'll need to repeatedly reference wy_data
        #!!! I want to find a better way of loading wy_data - maybe load only data for spacegroup_options?
        self.wy_data = loadWyckoffData().values

    def new_sites(self, spacegroup=None):

        # This section of code is checking the spacegroup input
        # if a spacegroup is not specified, grab a random one from our options
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)
        #!!! do I need to check this? This may slow the algorithm, but ensures a user doesn't break the function
        # if a spacegroup is specified, we still need to make sure it's valid
        else:
            check = spacegroup not in self.spacegroups_invalid
            # if it is invalid, print a message and quit the function
            if not check:
                # print('This spacegroup is invalid for the given composition') #!!! consider adding a warning
                return False

        # we need to grab the generators, wyckoff combinations, wyckoff group information for selected spacegroup
        coords_generator = self.coords_generators[spacegroup]
        wy_groupcombos = self.wy_groupcombos[spacegroup]
        wy_groupinfo = self.wy_groupinfo[spacegroup]

        # randomly grab a wy_group combination
        # NOTE: this does not have equal probability of grabbing all wyckoff site combinations because some wy_groups have more wy_site posibilities than others
        # choice(sg_combos['ValidCombinations']) doesn't work here, so we grab a random index instead
        random_index = randint(0, len(wy_groupcombos))
        wy_group_combo = wy_groupcombos[random_index]

        # make an empty list to store all the fractional coordinates
        coords_list = []  # regular list.append is faster than numpy.append
        # as well as an empty list for the species
        species_list = []

        # now we need to iterate through each element in stoich, see which wy_group(s) it was assigned to
        for i, wy_groups in enumerate(wy_group_combo):
            # wy_groups represents the combination of wy_group's for a single element
            # len(stoich) == len(wy_group_combo) because indexes are matched up (i.e. stoich[1] was assigned wy_group_combo[1])
            # so we can use the index of wy_groups to grab the element
            element = self.composition.elements[i]
            # wy_groups can be a list of wy_group entries
            for wy_group in wy_groups:
                # now we need to generate the coordinates for this wy_site
                # for that, we need three things:
                # (1) a random wy_site from the assigned wy_group
                # (2) the base wy_site coords corresponding to that wy_site (i.e. (x,y,z) or (0,y,0))
                # (3) random coords that exist inside the asymmetric unit, used to eval() the coords with
                # (4) ensure that the result coordinates have not been used already
                # wy_group label is a key to the wy_groupinfo dictionary
                # the wy_sites output is a list of indexes (as numpy array) that correspond to indicies in the loadWyckoffData() output
                wy_sites = wy_groupinfo[wy_group]
                check = False
                while not check:
                    # randomly choose one of these wy_site indexes
                    # I have this inside the while-loop because if a special wy_site (i.e. (0,0,0)) is picked when it's already in coords_used, we will get stuck in the while loop
                    wy_site_i = choice(wy_sites)
                    # use the choice to grab the wy_site
                    wy_site = self.wy_data[wy_site_i]
                    # grab the first entry (as all others are symmetrically equivalent) for coord template
                    wy_coords = wy_site[5]  # index 5 is 'Coordinates'
                    # generate random x,y,z values that are inside the asymmetric unit
                    x, y, z = coords_generator.new_vector()
                    # place these x,y,z values into the coords where necessary
                    # not sure why I need to use None,dict(x=x,y=y,z=z) inside eval. Eval() can't use the locals for some reason.
                    final_coords = eval(wy_coords, None, dict(x=x, y=y, z=z))
                    # see if the result is already a coordinate used
                    check = final_coords not in coords_list
                # append the coords and species to our output lists
                coords_list.append(final_coords)
                species_list.append(element)

        # maybe make these into pymatgen Site objects? I don't see any advantage to Site object,
        # because we will later need PeriodicSite objects and there's no direct conversion method
        return species_list, coords_list


##############################################################################

# Grab the boundry conditions for the asymmetric unit of a spacegroup's unitcell
def asymmetric_unit_boundries(spacegroup, asym_data=loadAsymmetricUnitData()):

    # spacegroup = spacegroup that we are interested in
    # asym_data = result of loadAsmmetricUnitData() - this is in the header for speed reasons

    # grab the asymmetric unit conditons from the asym_data
    # the array indicies (0-229) correspond to all spacegroups (1-230) respectively.
    # So if I want data for spacegroup 230, I need index 229 (i.e. spacegroup-1)
    asym_bounds = asym_data[spacegroup - 1]

    # convert the string of asym_data into a list of boundry conditions that we can test
    # so here we change things to something python can read and iterate through
    asym_bounds = asym_bounds.replace("≤", "<=")  # convert symbols
    # Is there a way I can do these next three lines in a single command...?
    # or maybe only run them for the spacegroups that need them?
    asym_bounds = asym_bounds.replace("2y", "(2*y)")  # convert
    asym_bounds = asym_bounds.replace("2x", "(2*x)")  # convert
    asym_bounds = asym_bounds.replace("-4x", "(-4*y)")  # convert
    asym_bounds = asym_bounds.split(";")  # convert str into a list

    return asym_bounds
