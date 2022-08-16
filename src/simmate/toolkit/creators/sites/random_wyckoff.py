# -*- coding: utf-8 -*-

import logging

from numpy.random import choice, randint
from tqdm import tqdm

from simmate.toolkit import Composition
from simmate.toolkit.creators.vector import UniformlyDistributedVectors
from simmate.toolkit.symmetry.wyckoff import (
    findValidWyckoffCombos,
    loadAsymmetricUnitData,
    loadWyckoffData,
)


class RandomWySites:
    def __init__(
        self,
        composition: Composition,
        spacegroup_include: list[int] = range(1, 231),
        spacegroup_exclude: list[int] = [],
        coords_generation_method=UniformlyDistributedVectors,
        # note, asymmetric_unit_boundries is included in coords_gen_options
        # automatically so this input is anything extra.
        coords_gen_options: dict = dict(),
        lazily_generate_combinations: bool = True,
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
        # I want the combinations and info to be stored as a dictionary of
        # {spacegroup:combos/info} entries.
        # We split this into 2 dictionaries becuase we reference each a lot and
        # it makes the code below easier.
        self.wy_groupinfo = {}
        self.wy_groupcombos = {}
        # some spacegroups will be incompatible with the given composition, so
        # we keep a list of these
        self.spacegroups_invalid = []

        # Each spacegroup will have a "generator" that manages possible wyckoff
        # combinations and the asymmetric unit associated with the spacegroup.
        # These will be stored as a dictionary of  {spacegroup: generator}
        self.coords_generators = {}
        # Options set in coords_gen_options will apply to all spacegroups, so
        # we store these up front. This because these generators are
        # sometimes accessed lazily
        self.coords_generation_method = coords_generation_method
        self.coords_gen_options = coords_gen_options

        # Generating all wyckoff combinations can take a long time to run in
        # some cases (e.g. high atom counts), so we may want to do it up front.
        # There are also scenarios where we don't want to generate the possible
        # spacegroup combinations until the spacegroup is actually requested.
        # This saves us time when we want just one structure and then are
        # done with this system.
        self.lazily_generate_combinations = lazily_generate_combinations
        if not lazily_generate_combinations:
            logging.info("Generating Wyckoff combinations for every spacegroup")
            # use tqdm to track progress
            for spacegroup in tqdm(self.spacegroup_options):
                self._setup_spacegroup_wyckoff_generator(
                    spacegroup,
                    show_logging=False,
                )
            logging.info("Done.")

        # below, I'll need to repeatedly reference wy_data
        #!!! I want to find a better way of loading wy_data - maybe load
        # only data for spacegroup_options?
        self.wy_data = loadWyckoffData().values

    def new_sites(self, spacegroup=None):

        # parse spacegroup or grab a random one (with necessary lazy-setup)
        spacegroup = self._init_spacegroup(spacegroup)
        # exit if we have an invalid spacegroup
        if not spacegroup:
            return False

        # we need to grab the generators, wyckoff combinations, wyckoff group
        # information for selected spacegroup
        coords_generator = self.coords_generators[spacegroup]
        wy_groupcombos = self.wy_groupcombos[spacegroup]
        wy_groupinfo = self.wy_groupinfo[spacegroup]

        # randomly grab a wy_group combination
        # NOTE: this does not have equal probability of grabbing all wyckoff
        # site combinations because some wy_groups have more wy_site p
        # osibilities than others.
        # choice(sg_combos['ValidCombinations']) doesn't work here, so we grab
        # a random index instead
        random_index = randint(0, len(wy_groupcombos))
        wy_group_combo = wy_groupcombos[random_index]

        # make an empty list to store all the fractional coordinates
        coords_list = []  # regular list.append is faster than numpy.append
        # as well as an empty list for the species
        species_list = []

        # now we need to iterate through each element in stoich, see which
        # wy_group(s) it was assigned to
        for i, wy_groups in enumerate(wy_group_combo):
            # wy_groups represents the combination of wy_group's for a single element
            # len(stoich) == len(wy_group_combo) because indexes are matched
            # up (i.e. stoich[1] was assigned wy_group_combo[1])
            # so we can use the index of wy_groups to grab the element
            element = self.composition.elements[i]
            # wy_groups can be a list of wy_group entries
            for wy_group in wy_groups:
                # now we need to generate the coordinates for this wy_site
                # for that, we need three things:
                # (1) a random wy_site from the assigned wy_group
                # (2) the base wy_site coords corresponding to that wy_site
                #     (i.e. (x,y,z) or (0,y,0))
                # (3) random coords that exist inside the asymmetric unit,
                #     used to eval() the coords with
                # (4) ensure that the result coordinates have not been used already
                # wy_group label is a key to the wy_groupinfo dictionary
                # the wy_sites output is a list of indexes (as numpy array)
                # that correspond to indicies in the loadWyckoffData() output
                wy_sites = wy_groupinfo[wy_group]
                check = False
                while not check:
                    # randomly choose one of these wy_site indexes
                    # I have this inside the while-loop because if a special
                    # wy_site (i.e. (0,0,0)) is picked when it's already in
                    # coords_used, we will get stuck in the while loop
                    wy_site_i = choice(wy_sites)
                    # use the choice to grab the wy_site
                    wy_site = self.wy_data[wy_site_i]
                    # grab the first entry (as all others are symmetrically
                    # equivalent) for coord template
                    wy_coords = wy_site[5]  # index 5 is 'Coordinates'
                    # generate random x,y,z values that are inside the
                    # asymmetric unit
                    x, y, z = coords_generator.new_vector()
                    # place these x,y,z values into the coords where necessary
                    # not sure why I need to use None,dict(x=x,y=y,z=z)
                    # inside eval. Eval() can't use the locals for some reason.
                    final_coords = eval(wy_coords, None, dict(x=x, y=y, z=z))
                    # see if the result is already a coordinate used
                    check = final_coords not in coords_list
                # append the coords and species to our output lists
                coords_list.append(final_coords)
                species_list.append(element)

        # maybe make these into pymatgen Site objects? I don't see any
        # advantage to Site object, because we will later need PeriodicSite
        # objects and there's no direct conversion method
        return species_list, coords_list

    def _init_spacegroup(self, spacegroup):
        # This checks the spacegroup input from a user or grabs a random one.
        # We isolate this into a separate class because of the complex logic
        # required to handle lazy

        # if a spacegroup is not specified, grab a random one from our options
        if not spacegroup:
            # If we generated the combinatons up front, we can just grab a spacegroup
            # from all the valid options.
            if not self.lazily_generate_combinations:
                spacegroup = choice(self.spacegroup_options)

            # Otherwise, we need to randomly select a symmetry system until we
            # find a valid one
            else:
                spacegroup = -1  # gives non-existing spacegroup to start the loop

                # check if the spacegroup is valid & analyzed before
                while not spacegroup in self.coords_generators:

                    # bug-note: this loop should not go on endlessly, because
                    # spacegroup=1 should **always** be valid and it will be
                    # selected eventually in extreme cases.

                    # grab a new spacegroup
                    spacegroup = choice(self.spacegroup_options)

                    # generate the possible combinations.
                    self._setup_spacegroup_wyckoff_generator(spacegroup)

        # if the user provided a spacegroup, we still need to check if its been
        # analyzed and is valid.
        else:

            # make sure wyckoff combos have been analyzed before
            if (
                self.lazily_generate_combinations
                and spacegroup not in self.coords_generators
                and spacegroup not in self.spacegroups_invalid
            ):
                # generate the possible combinations.
                self._setup_spacegroup_wyckoff_generator(spacegroup)

            # Make sure the spacegroup is valid for the given composition
            if spacegroup in self.spacegroups_invalid:
                logging.warning(
                    f"Spacegroup {spacegroup} is invalid for {self.composition}"
                )
                return False

        return spacegroup

    def _setup_spacegroup_wyckoff_generator(
        self, spacegroup: int, show_logging: bool = True
    ):
        if show_logging:
            logging.info(
                f"Generating possible wyckoff combinations for spacegroup {spacegroup}"
            )
        sg_combo_data = findValidWyckoffCombos(self.stoichiometry, spacegroup)
        if show_logging:
            logging.info("Done generating combinations.")
        # If the spacegroup + stoich combination has no valid combinations,
        # the generator will not work
        if not sg_combo_data["ValidCombinations"]:
            self.spacegroups_invalid.append(spacegroup)
            # we also need to update all the spacegroup_options now that we have
            # a new invalid one.
            self.spacegroup_options = [
                sg
                for sg in self.spacegroup_options
                if sg not in self.spacegroups_invalid
            ]
            # exit the function -- false indicates we have an invalid spacegroup
            return False
        # Otherwise we have valid combos that we want to store -- so that
        # we don't need to calculate them again.
        self.wy_groupinfo.update({spacegroup: sg_combo_data["WyckoffGroups"]})
        self.wy_groupcombos.update({spacegroup: sg_combo_data["ValidCombinations"]})

        # Next we need to setup the asymmetric unit boundry conditions.

        # grab a copy of the user inputs for reference
        # we will manipulate final_options for each spacegroup for use
        # in the generator
        final_options = self.coords_gen_options.copy()

        # establish the coords generator with asymmetric_unit_boundries
        # this process is a little more complicated because we require
        # that the asymmetric_unit_boundries be included in extra_conditions
        asym_bounds = asymmetric_unit_boundries(spacegroup)

        # if any extra_conditions were provided by the user, we want to
        # combine them with the asym conditions
        if "extra_conditions" in self.coords_gen_options.keys():
            all_bounds = self.coords_gen_options["extra_conditions"] + asym_bounds
            final_options.update({"extra_conditions": all_bounds})
        # otherwise, the asym_bounds are the only boundry conditions for
        # the coordinates
        else:
            final_options.update({"extra_conditions": asym_bounds})

        # now that we have the coords_gen_options updated, we can make the generator
        coords_generator = self.coords_generation_method(**final_options)

        # add store this generator
        self.coords_generators.update({spacegroup: coords_generator})

        # exit the function -- true indicates we have a valid spacegroup
        return True


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
