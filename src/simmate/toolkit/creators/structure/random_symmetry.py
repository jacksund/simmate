# -*- coding: utf-8 -*-

import logging

from numpy.random import choice

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.lattice import RSLSmartVolume
from simmate.toolkit.creators.sites.random_wyckoff import RandomWySites
from simmate.toolkit.creators.structure.base import StructureCreator
from simmate.toolkit.creators.utils import NestedFixes
from simmate.toolkit.validators.structure import SiteDistanceMatrix


class RandomSymStructure(StructureCreator):

    # BUG: because I use MultiplicityPrimitive in RandomWySites but make a
    # convential cell below, there may be a issue with the input composition
    # vs. output composition number of sites. For example, when making a Ca2N
    # structure with spacegroup 166, the conventional cell will give a
    # structure of Ca6N3. I can then convert this to the primitive cell to get
    # Ca2N, but depending on the sym settings that I use, this might not work.
    # I don't currently have structure.get_primitive_structure() in this creator
    # because it will break the Generator workflow (which assumes unchanging
    # cell between validations).

    def __init__(
        self,
        composition: Composition,
        spacegroup_include: list[int] = range(1, 231),
        spacegroup_exclude: list[int] = [],
        lattice_generation_method=RSLSmartVolume,
        lattice_gen_options: dict = {},
        site_generation_method=RandomWySites,
        site_gen_options: dict = {},
        validator_method=SiteDistanceMatrix,
        validator_options: dict = {},
        fixindicator_method=NestedFixes,
        fixindicator_options: dict = {
            "fixes": ["new_lattice", "new_sites"],
            "cutoffs": [15, 100],
        },
        remove_failed_spacegroups: bool = False,
        cleanup: bool = True,
    ):

        # sg_include = list of spacegroups that we are interested in. Default
        # is all 230 spacegroups
        # sg_exclude = list of spacegroups that we should explicitly ignore

        # method settings
        self.remove_failed_spacegroups = remove_failed_spacegroups
        self.removed_spacegroups = []
        self.cleanup = cleanup

        # save the composition for reference
        self.composition = composition

        # establish the lattice generation method and use the specified options
        # many methods include options for spacegroup_include/exclude
        # we want to override those options with what the user indicated here
        lattice_gen_options.update(
            dict(
                composition=composition,
                spacegroup_include=spacegroup_include,
                spacegroup_exclude=spacegroup_exclude,
            )
        )
        self.lattice_generator = lattice_generation_method(**lattice_gen_options)

        # establish the site generation method and use the specified options
        # many methods include options for composition and spacegroup_include/exclude
        # we want to override those options with what the user indicated here
        site_gen_options.update(
            dict(
                composition=composition,
                spacegroup_include=spacegroup_include,
                spacegroup_exclude=spacegroup_exclude,
            )
        )
        self.site_generator = site_generation_method(**site_gen_options)

        # BUG: I assume that all lattice/site methods have three inputs
        # which will cause errors when the new classes that don't accept these
        # this input types.

        # establish the validation method and use the specified options
        # many methods include options for composition
        # we want to override that option with what the user indicated here
        validator_options.update(dict(composition=composition))
        self.validator = validator_method(**validator_options)

        # establish the FixIndicator method and use the specified options
        self.fixindicator = fixindicator_method(**fixindicator_options)

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

        # While a given sg_inlcude and sg_exclude were given, some spacegroup
        # may not be compatible with the lattice or site method used. For example,
        # the spacegroup 230 is not possible with a composition of MgSiO3 (1:1:3).
        # Selection of appropriate wy_sites can't be done. The user still may
        # have 230 in the spacegroup_include. This function will ensure all
        # spacegroups are compatible -- if not, self.spacegroup_options will be
        # updated by remove the spacegroup. Therefore, this step is to see
        # which spacegroups are compatible with BOTH the lattice creation method
        # and the site creation method.
        self.spacegroup_options = [
            sg
            for sg in self.spacegroup_options
            if sg in self.lattice_generator.spacegroup_options
            and sg in self.site_generator.spacegroup_options
        ]
        # !!! should I have a self.spacegroups_invalid list to keep track of
        # what's been removed?
        #
        # BUG: this requires all site and lattice creators to have a
        # spacegroup_options property.

    def create_structure(self, spacegroup=None):

        # If a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible
        # with the vector_generator built
        if not spacegroup:
            # randomly select a spacegroup
            spacegroup = choice(self.spacegroup_options)
        logging.info(f"Creating structure with spacegroup {spacegroup}")

        # Use the lattice generator to make a starting lattice
        lattice = self.lattice_generator.new_lattice(spacegroup)

        # Use the site generator to make a starting series of sites
        sites = self.site_generator.new_sites(spacegroup)
        # if the generator returns None - then the spacegroup is incompatible
        # with the composition
        if not sites:
            # The spacegroup is incompatible with the composition and
            # site-generator-method.
            # We do not raise an error in case this method needs to be called
            # on a guess/check basis.
            return False
        # otherwise, the generator was successful so we can unpack its output
        species, coords = sites

        # Set the valid_struct to false so we can start the loop below.
        is_valid = False
        # Keep track of the number of attempts we make to create a structure
        attempts = 0

        # we want to continue this loop until we get a valid structure
        while not is_valid:

            # add an attempt to the validator
            attempts += 1

            # since we only have sites in the asym unit, we use symmetry
            # operations to get the rest of the unitcell
            structure = Structure.from_spacegroup(spacegroup, lattice, species, coords)
            # BUG: Note that I'm not always limiting sites to the asym unit...
            # if I used RandomSites instead of RandomSymSites or RandomWySites,
            # this may give problems

            # Check that the structure is valid
            is_valid = self.validator.check_structure(structure)

            # If the validator passes, we can exit the loop!
            # This will be done automatically when 'while not is_valid' is checked

            # Otherwise, we need to try to fix the structure and check it again.
            if not is_valid:

                # see the assigned 'fix' for the validator
                fix = self.fixindicator.point_to_fix(attempts)

                if not fix:
                    # if the 'fix' is False, that means we maxed out the attempts
                    # on the validator.
                    # this indicates a total failure and the function should end
                    structure = False  # set to false indicating a failure
                    break  # exits the while loop with structure = False
                    # We do not return False yet because we want to
                    # I could return False here because we want to check for
                    # "remove_failed_spacegroups" below

                # The defualt "point_to_fix" settings have strings returned
                # and not objects. There are only a limited number of options
                # for the string returned -- e.g. "new_structure indicates
                # we making a new structure from scratch, while "new_lattice"
                # says to try changing up the lattice but keep the sites.
                elif fix == "new_structure":
                    # Use the lattice generator to make a starting lattice
                    lattice = self.lattice_generator.new_lattice(spacegroup)

                    # Use the site generator to make a starting series of sites
                    sites = self.site_generator.new_sites(spacegroup)
                    # if the generator returns None - then the spacegroup is
                    # incompatible with the composition
                    if not sites:
                        logging.warning(
                            f"Failed to create a structure using spacegroup {spacegroup}."
                        )
                        return False
                    # otherwise, the generator was successful so we can unpack
                    # its output
                    species, coords = sites

                elif fix == "new_lattice":
                    # Use the lattice generator to make a starting lattice
                    lattice = self.lattice_generator.new_lattice(spacegroup)

                elif fix == "new_sites":
                    # Use the site generator to make a starting series of sites
                    sites = self.site_generator.new_sites(spacegroup)
                    # if the generator returns None - then the spacegroup is
                    # incompatible with the composition
                    if not sites:
                        logging.warning(
                            f"Failed to create a structure using spacegroup {spacegroup}."
                        )
                        return False
                    # otherwise, the generator was successful so we can unpack
                    # its output
                    species, coords = sites

                # !!! Rather than using "new_structure", "new_lattice", and "new_sites"
                # like we do above, it would be more powerful to allow specific
                # settings of different creators or transformations. An example
                # of this would be using a `transformations.sites` class to
                # relax sites to a reasonable position. This code below is
                # a template for how this feature enhancement would look. I keep
                # it strictly as notes for now.
                #
                # fix_type = str(type(fix))
                # # if fix points to a generator, we want to use its .new_* method
                # if 'creators.structure' in fix_type:
                #     structure = fix.new_structure(spacegroup)
                #     # we need to update the lattice, species, coords
                #     # otherwise it will be rewritten above
                #     lattice = structure.lattice
                #     species = structure.species
                #     coords = structure.frac_coords.tolist()
                # elif 'creators.lattice' in fix_type:
                #     lattice = fix.new_lattice(spacegroup)
                # elif 'creators.sites' in fix_type:
                #     species, coords = fix.new_sites(spacegroup)
                # # if fix points to a transform, we want to use its apply_to_* method
                # elif 'transformations.structure' in fix_type:
                #     structure = fix.apply_to_structure(structure)
                #     # we need to update the lattice, species, coords otherwise
                #     # it will be rewritten above
                #     lattice = structure.lattice
                #     species = structure.species
                #     coords = structure.frac_coords.tolist()
                # elif 'transformations.lattice' in fix_type:
                #     lattice = fix.apply_to_lattice(structure.lattice)
                # elif 'transformations.sites' in fix_type:
                #     species, coords = fix.apply_to_sites(
                #         structure.species,
                #         structure.coords,
                #     )

        # If the structure creation failed (structure = False), then see if the
        # failed spacegroup should be removed from future choices.
        if not structure:
            logging.warning(
                f"Failed to create a structure using spacegroup {spacegroup}."
            )
            if self.remove_failed_spacegroups:
                logging.info(
                    f"Removed spacegroup {spacegroup} from options. "
                    "This will not be selected moving forward."
                )
                # add the removed spacegroup to our list for reference
                self.removed_spacegroups.append(spacegroup)
                # and remove the spacegroup from our list of options
                self.creator.spacegroup_options.remove(spacegroup)
        else:
            logging.info("Creation successful.")

        # Cleanup does 'fix-up' steps before returning the final structure.
        # This includes converting from the conventional cell to primitive as
        # well as sort the sites by electronegativity
        # Also make sure that structure != False
        if self.cleanup and structure:
            # convert the conventional unitcell to the primitive
            #!!! should I use a spacegroup analyzer instead?
            #!!! Should I LLL reduce?
            structure = structure.get_primitive_structure()
            # make sure the sites are sorted by electronegativity of their elements
            # this is important for some mutations
            structure.sort()  # this is faster than get_sorted_structure

        # BUG: In some cases, the stoichometry of the structure will be
        # different from the input composition. This happens when the structure
        # happens to have higher symmetry than the spacegroup it was made with.
        # For example, I could make a structure of Mg4Si4O12, but the primitive
        # cell has Mg2Si2O6 or MgSiO3. So we got back a structure with fewer
        # atoms than what we requested! This could cause issues down the line,
        # so we may want to check for this.
        # if structure.composition.num_atoms != composition.num_atoms:
        #     print('COMP ERROR')
        #     # restart the whole function
        #     structure = new_sample(spacegroup)
        #     # BUG: might hit a recursion depth error

        return structure
