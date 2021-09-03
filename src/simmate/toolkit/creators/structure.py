# -*- coding: utf-8 -*-

##############################################################################

from numpy.random import choice

from pymatgen.core.structure import Structure

# from pymatgen.analysis.structure_prediction.volume_predictor import DLSVolumePredictor #, RLSVolumePredictor

from pymatdisc.core.creators.base import StructureCreator
from pymatdisc.core.creators.lattice import RSLSmartVolume  # RandomSymLattice
from pymatdisc.core.creators.sites import RandomWySites
from pymatdisc.core.creators.utils import NestedFixes

from pymatdisc.core.validators.structure import SiteDistanceMatrix

##############################################################################

#!!!!!!!!!!!!!!!!!!!!!!!!
# MAJOR POTENTIAL BUG
# because I use MultiplicityPrimitive in RandomWySites but make a convential cell below,
# there may be a issue with the input composition vs. output composition number of sites.
# For example, when making a Ca2N structure with spacegroup 166, I will be given
# a structure of Ca6N3. I can then convert this to the primitive cell to get Ca2N, but
# depending on the sym settings that I use, this might not work.
# I don't currently have structure.get_primitive_structure() in this creator
# because it will break the Generator workflow (which assumes unchanging cell between validations).
#!!!!!!!!!!!!!!!!!!!!!!!!


class RandomSymStructure(StructureCreator):

    #!!! I assume that all lattice/site methods have three inputs (see init below), which will cause errors... TO-DO

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
        lattice_generation_method=RSLSmartVolume,
        lattice_gen_options={},
        site_generation_method=RandomWySites,
        site_gen_options={},
        validator_method=SiteDistanceMatrix,
        validator_options={},
        fixindicator_method=NestedFixes,
        fixindicator_options={
            "fixes": ["new_lattice", "new_sites"],
            "cutoffs": [15, 100],
        },
        remove_failed_spacegroups=False,
        cleanup=True,
    ):

        # sg_include = list of spacegroups that we are interested in. Default is all 230 spacegroups
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

        # While a given sg_inlcude and sg_exclude were given, some spacegroup may not be compatible
        # with the lattice or site method use. For example, the spacegroup 230 is not possible
        # with a composition of MgSiO3 (1:1:3). Selection of appropriate wy_sites can't be done.
        # The user still may have 230 in the spacegroup_include. This function will ensure all spacegroups
        # are compatible -- if not, self.spacegroup_options will be updated by remove the spacegroup.
        # see which spacegroups are compatible with the lattice creation method and update
        # see which spacegroups are compatible with the site creation method and
        #!!! should I have a self.spacegroups_invalid list to keep track of what's been removed?
        #!!! ERROR WILL BE THROWN IF I DON'T REQUIRE ALL SITE AND LATTICE CREATORS TO HAVE spacegroup_options LISTED!!!
        self.spacegroup_options = [
            sg
            for sg in self.spacegroup_options
            if sg in self.lattice_generator.spacegroup_options
            and sg in self.site_generator.spacegroup_options
        ]

    def create_structure(self, spacegroup=None):

        # If a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a spacegroup
            spacegroup = choice(self.spacegroup_options)

        # Use the lattice generator to make a starting lattice
        lattice = self.lattice_generator.new_lattice(spacegroup)

        # Use the site generator to make a starting series of sites
        sites = self.site_generator.new_sites(spacegroup)
        # if the generator returns None - then the spacegroup is incompatible with the composition
        if not sites:
            # print('The spacegroup is incompatible with the composition and site-generator-method')
            # REPORT POTENTIAL ISSUE IF THIS POINT IS REACHED
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
            #!!! Should this be at the bottom of the while loop? So the first attempt is 0?
            attempts += 1

            # since we only have sites in the asym unit, we use symmetry operations to get the rest of the unitcell
            #!!! NOTE that I'm not always limiting sites to the asym unit... if I used RandomSites instead of RandomSymSites or RandomWySites, this may give problems
            structure = Structure.from_spacegroup(spacegroup, lattice, species, coords)

            # Check that the structure is valid
            is_valid = self.validator.check_structure(structure)

            # If the validator passes, we can exit the loop!
            # This will be done automatically when 'while not is_valid' is checked

            # Otherwise, we need to try to fix the structure and check it again
            if not is_valid:

                # see the assigned 'fix' for the validator
                fix = self.fixindicator.point_to_fix(attempts)

                if not fix:
                    # if the 'fix' is False, that means we maxed out the attempts on the validator
                    # this indicates a total failure and the function should end
                    structure = False  # set to false indicating a failure
                    break  # exits the while loop with structure = False
                    # alternatively, I could return False here

                # The defualt settings have strings returned, not objects.
                # This could tell the function to try making a new structure from
                # scratch or maybe changing up the lattice.
                # if type(fix) == str:
                if fix == "new_structure":
                    # Use the lattice generator to make a starting lattice
                    lattice = self.lattice_generator.new_lattice(spacegroup)

                    # Use the site generator to make a starting series of sites
                    sites = self.site_generator.new_sites(spacegroup)
                    # if the generator returns None - then the spacegroup is incompatible with the composition
                    if not sites:
                        # print('The spacegroup is incompatible with the composition and site-generator-method')
                        # REPORT POTENTIAL ISSUE IF THIS POINT IS REACHED
                        return False
                    # otherwise, the generator was successful so we can unpack its output
                    species, coords = sites
                elif fix == "new_lattice":
                    # Use the lattice generator to make a starting lattice
                    lattice = self.lattice_generator.new_lattice(spacegroup)
                elif fix == "new_sites":
                    # Use the site generator to make a starting series of sites
                    sites = self.site_generator.new_sites(spacegroup)
                    # if the generator returns None - then the spacegroup is incompatible with the composition
                    if not sites:
                        # print('The spacegroup is incompatible with the composition and site-generator-method')
                        # REPORT POTENTIAL ISSUE IF THIS POINT IS REACHED
                        return False
                    # otherwise, the generator was successful so we can unpack its output
                    species, coords = sites

                # # we need to know if the fix is a transformation or a creation type
                # #!!! there should be a better way to do this. Such as a check on is-child-class..?
                # fix_type = str(type(fix))
                # # if fix points to a generator, we want to use its .new_* method
                # if 'creators.structure' in fix_type:
                #     structure = fix.new_structure(spacegroup)
                #     # we need to update the lattice, species, coords otherwise it will be rewritten above
                #     lattice = structure.lattice
                #     species = structure.species
                #     coords = structure.frac_coords.tolist() #!!! bug with numpy array vs python list
                # elif 'creators.lattice' in fix_type:
                #     lattice = fix.new_lattice(spacegroup)
                # elif 'creators.sites' in fix_type:
                #     species, coords = fix.new_sites(spacegroup)

                # # if fix points to a transform, we want to use its apply_to_* method
                # elif 'transformations.structure' in fix_type:
                #     structure = fix.apply_to_structure(structure)
                #     # we need to update the lattice, species, coords otherwise it will be rewritten above
                #     lattice = structure.lattice
                #     species = structure.species
                #     coords = structure.frac_coords.tolist() #!!! bug with numpy array vs python list
                # elif 'transformations.lattice' in fix_type:
                #     lattice = fix.apply_to_lattice(structure.lattice)
                # elif 'transformations.sites' in fix_type:
                #     species, coords = fix.apply_to_sites(structure.species, structure.coords)

                # regardless of what the next step was, we are going to restart the while-loop

        # If the structure creation failed (structure = False), then see if the
        # failed spacegroup should be removed from future choices.
        if not structure and self.remove_failed_spacegroups:
            print(
                "This generator failed to create a structure using spacegroup {}. This spacegroup will be removed from the list of randomly selected spacegroups moving forward.".format(
                    spacegroup
                )
            )
            # add the removed spacegroup to our list for reference
            self.removed_spacegroups.append(spacegroup)
            # and remove the spacegroup from our list of options
            self.creator.spacegroup_options.remove(spacegroup)

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

        #!!! In some cases, the stoichometry of the structure will be different from the input composition.
        # This happens when the structure happens to have higher symmetry than the spacegroup it was made with.
        # For example, I could make a structure of Mg4Si4O12, but the primitive cell has Mg2Si2O6 or MgSiO3.
        # So we got back a structure with fewer atoms than what we requested! This could cause issues down the
        # line, so we may want to check for this.
        # if structure.composition.num_atoms != composition.num_atoms:
        #     print('COMP ERROR')
        #     structure = new_sample(spacegroup) # restart the whole function # might hit a recursion depth error

        return structure


##############################################################################


class PyXtalStructure(StructureCreator):

    # see docs: https://pyxtal.readthedocs.io/en/latest/index.html

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object,
        volume_factor=1.0,
        lattice=None,
        tolerance_matrix=None,  # options unique to PyXtal's random_crystal
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
    ):

        #!!! this is inside the init because not all users will have this installed!
        try:
            from pyxtal.crystal import random_crystal
        except ModuleNotFoundError:
            #!!! I should raise an error in the future
            print("You must have PyXtal installed to use PyXtalStructure!!")
            return  # exit the function as the script will fail later on otherwise

        # save the module for reference below
        self.pyxtal = random_crystal

        # save the composition information in the format that PyXtal wants ['Ca', 'N']
        self.species = [element.symbol for element in composition.elements]
        # save the number of Ions in the format that PyXtal wants [3,2]
        self.numIons = [
            int(composition[element.symbol]) for element in composition.elements
        ]
        # save the volume factor to be used later
        self.volume_factor = volume_factor
        # if the user supplied a lattice, it should be a 3x3 matrix -- NOT a pymatgen lattice object
        #!!! should I add a check that this is a matrix here?
        self.lattice = lattice
        #!!! TO-DO: I need to allow the user to specify the tolerance matrix
        if tolerance_matrix:
            print(
                "PyMatDisc's wrapper for PyXtal does not currently support setting "
                "the tolerance matrix for PyXtal's random_crystal(). If you want this "
                "option added, please contact the PyMatDisc developers."
            )

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

    def create_structure(self, spacegroup=None):

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # now make the new structure using PyXtal's crystal.random_crystal function
        # NOTE: all of these options are set in the init except for the spacegroup
        structure = self.pyxtal(
            group=int(
                spacegroup
            ),  #!!! why do I need int() here? This should already work without it...
            species=self.species,
            numIons=self.numIons,
            factor=self.volume_factor,
            lattice=self.lattice,
        )
        # tm=<pyxtal.crystal.Tol_matrix object> # not supported right now!

        # note that we have a PyXtal structure object, not a PyMatGen one!
        # The PyXtal structure has a *.valid feature that lets you know if structure creation was a success
        # so we will check that
        if structure.valid:
            # if it is valid, we want the PyMatGen structure object, which is at *.struct
            return structure.struct
        else:
            # if it is not valid, the structure creation failed
            return False


##############################################################################


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

        # I estimate the volume using some code I wrote
        #!!! this code will likely move in the future!
        from pymatdisc.core.estimate import estimate_volume

        volume_guess = estimate_volume(composition)

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


##############################################################################


class GASPStructure:

    # see source: https://github.com/henniggroup/GASP-python
    # see tutorials: https://github.com/henniggroup/GASP-python/blob/master/docs/usage.md

    #!!! The documentation and code organization is pretty difficult to follow for GASP,
    #!!! so I don't include any of their options. Instead, I assume all default values
    #!!! for a fixed composition. There's not much I can do about this until GASP fixes
    #!!! the organization of their code and add documentation. As-is, GASP is not ment to
    #!!! be used as a python module, which really hinders its reusability.

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
    ):

        #!!! this is inside the init because not all users will have this installed!
        try:
            from gasp.general import CompositionSpace, IDGenerator
            from gasp.development import Constraints
            from gasp.organism_creators import RandomOrganismCreator
        except ModuleNotFoundError:
            #!!! I should raise an error in the future
            print("You must have GASP installed to use GASPStructure!!")
            return  # exit the function as the script will fail later on otherwise

        # generate the inputs required for GASP to make a new structure
        #!!! I assume all defaults for GASP right now
        self.composition_space = CompositionSpace([composition.formula])
        self.constraints = Constraints(
            None, self.composition_space
        )  #!!! TO-DO add distance matrix (I currently do this through generator)
        self.id_generator = IDGenerator()
        self.random_org_creator = RandomOrganismCreator(
            None, self.composition_space, self.constraints
        )

        #!!! GASP uses a random module as an input here... This should be fixed
        from numpy import random

        self.random = random

        # this creator doesnt use sym so P1 is the only option
        self.spacegroup_options = [1]

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: GASP does not allow for specification of atomic sites and your "
                "specification here will be overwritten."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While GASP allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: GASP does not use symmetry to generate their structures "
                "and specifying this has no effect."
            )

        # sometimes gasp fails to make a structure, but let's loop it until we get a valid one
        structure_gasp = False
        while not structure_gasp:
            # now make the new structure using gasp.organism_creators.RandomOrganismCreator
            #!!! currently this prints a message, which I can't mute
            structure_gasp = self.random_org_creator.create_organism(
                self.id_generator, self.composition_space, self.constraints, self.random
            )
        # # the output will be None if the creation failed
        # if not structure_gasp:
        #     # creation failed, so return false
        #     return False

        # Grab the cell object from the output
        structure_gasp = structure_gasp.cell

        # convert the gasp Cell object to pymatgen Structure
        # Cell is really a child of Structure, so I'm actually reducing functionality here
        structure = Structure(
            lattice=structure_gasp.lattice,
            species=structure_gasp.species,
            coords=structure_gasp.frac_coords,
        )

        return structure


##############################################################################

#!!! NOT TESTED
class AIRSSStructure:

    # see source: https://www.mtg.msm.cam.ac.uk/Codes/AIRSS
    # see tutorials: https://airss-docs.github.io/

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
    ):

        # see if the user has AIRSS installed
        import subprocess

        #!!! what is the best way to see if AIRSS is installed? Check the path?
        output = subprocess.run(
            "airss.pl",  # command that calls AIRSS
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )
        if output.returncode == 1:
            #!!! I should raise an error in the future
            print("You must have AIRSS installed to use AIRSSStructure!!")
            return  # exit the function as the script will fail later on otherwise

        # to setup the AIRSS creator, we need to make a *.cell file that
        # for example, a SiO2 file will look like... (NOTE - the # symbols should be include in the file)
        # VARVOL=35
        # SPECIES=Si%NUM=1,O%NUM=2
        # MINSEP=1.0 Si-Si=3.00 Si-O=1.60 O-O=2.58

        # lets make this file and name it after the composition
        self.cell_filename = (
            composition.formula.replace(" ", "") + ".cell"
        )  # .replace is to remove spaces

        # create the file
        file = open(self.cell_filename, "w")

        # first write the VARVOL line
        # I estimate the volume using some code I wrote
        #!!! this code will likely move in the future!
        from pymatdisc.core.estimate import estimate_volume

        volume = estimate_volume(composition)
        # write the line
        file.write("#VARVOL={}".format(volume) + "\n")

        # write the SPECIES line
        line = "#SPECIES="
        for element in composition:
            line += element.symbol + "%NUM=" + str(int(composition[element])) + ", "
        line = line[:-2]  # remove the final ', '
        # write the line
        file.write(line + "\n")

        # write the MINSEP line
        #!!! TO-DO for now I just assume 1 Angstrom
        file.write("#MINSEP=1.0" + "\n")

        # close the file
        file.close()

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: AIRSS does not allow for specification of atomic sites and your "
                "specification here will be overwritten."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While AIRSS allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: AIRSS does not use symmetry to generate their structures "
                "and specifying this has no effect."
            )

        # now make the new structure using AIRSS scripts
        # NOTE: all of these options are set in the init except for the spacegroup
        #!!! should I add a timelimit?
        #!!! if I want to make this so I can make structures in parallel, I should reoranize the cif output naming
        import subprocess

        output = subprocess.run(
            "buildcell < {} | cabal cell cif > AIRSS_output.cif".format(
                self.cell_filename
            ),  # command that calls AIRSS #!!! subprocess prefers a list - should I change this?
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )

        # check to see if it was successful
        if output.returncode == 1:
            # AIRSS failed to make the structure
            return False

        # convert the cif file to pymatgen Structure
        structure = Structure.from_file("AIRSS_output.cif")

        # and delete the cif file for cleanup
        import os

        os.remove("AIRSS_output.cif")

        return structure


##############################################################################

#!!! NOT TESTED
class XtalOptStructure:

    # This wrapper actually uses the submodule randSpg written by XtalOpt devs
    # see source: https://github.com/xtalopt/randSpg
    # see tutorials: https://github.com/zbwang/randSpg/commit/73d2f33fc69da531398bf395dbfff581f4dbacad

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        spacegroup_include=range(1, 231),
        spacegroup_exclude=[],
    ):

        # make a list of spacegroups that we are allowed to choose from
        #!!! should I add a check to see if each spacegroup option is compatible with the composition?
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

        #!!! this is inside the init because not all users will have this installed!
        try:
            from pyrandspg import RandSpgInput, LatticeStruct, RandSpg

            # save for reference later
            self.RandSpgInput = RandSpgInput
            self.RandSpg = RandSpg
        except ModuleNotFoundError:
            #!!! I should raise an error in the future
            print(
                "You must have XtalOpt installed to use XtalOptStructure!! More specifically, this wrapper"
                " uses the randSpg submodule of XtalOpt and the python bindings made for it (pyrandspg)."
            )
            return  # exit the function as the script will fail later on otherwise

        # first establish the min/max values for the lattice vectors and angles
        #!!! change these to user inputs in the future
        # There's no fixed volume setting for XtalOpt so I need to set a minVol, maxVol, and vector limits
        from pymatdisc.core.estimate import estimate_volume, estimate_radii

        volume = estimate_volume(composition)
        # set the limits on volume (should I do this?)
        self.min_volume = volume * 0.5
        self.max_volume = volume * 1.5
        # let's set the minimum to the smallest radii
        min_vector = min(estimate_radii(composition))
        # let's set the maximum to volume**0.8 #!!! This is a huge range and I should test this in the future
        max_vector = volume ** 0.8
        self.lattice_min = LatticeStruct(
            min_vector, min_vector, min_vector, 60.0, 60.0, 60.0
        )  # a,b,c,alpha,beta,gamma
        self.lattice_max = LatticeStruct(
            max_vector, max_vector, max_vector, 120.0, 120.0, 120.0
        )

        # Format composition in the manner randspg request it.
        # This is a list of atomic numbers (for example, MgSiO3 is [12, 14, 8, 8, 8])
        self.atomic_nums = [
            element.number
            for element in composition
            for x in range(int(composition[element]))
        ]

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: While XtalOpt allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While GASP allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # now make the new structure using gasp.organism_creators.RandomOrganismCreator
        # establish input settings
        #!!! other options that I can add (I should have these in init above)
        #!!! see https://github.com/xtalopt/randSpg/blob/master/python/pyrandspg.cpp
        #   IADScalingFactor, minRadius, manualAtomicRadii, customMinIADs, minVolume, maxVolume,
        #   forcedWyckAssignments, verbosity, maxAttempts, forceMostGeneralWyckPos
        #!!! if there's only one spacegroup option, I could speed this up by moving it to the init
        #!!! For some reason, I can't use kw arguments... I'm forced to list inputs
        input_settings = self.RandSpgInput(
            spacegroup,
            self.atomic_nums,
            self.lattice_min,
            self.lattice_max,
        )
        # because I can't use keywords in the input above, I need to set this here...
        input_settings.forceMostGeneralWyckPos = False  #!!! Do I want this?
        input_settings.maxAttempts = 1000  # default is 100 but leads to many failures
        input_settings.minVolume = self.min_volume
        input_settings.maxVolume = self.max_volume

        structure_randspg = self.RandSpg.randSpgCrystal(input_settings)

        # Even if the generation fails, an object is still returned.
        # We therefore need to catch failed structures by looking at the
        # numAtoms. If that indicates there are zero atoms, then we know the creation failed
        if structure_randspg.numAtoms() == 0:
            # failed to make a structure
            return False

        # convert the randspg object to pymatgen Structure
        poscar_str = structure_randspg.getPOSCARString()
        structure = Structure.from_str(
            poscar_str, "poscar"
        )  #!!! if this doesn't work, use .from_file(...writePOSCAR())

        return structure


##############################################################################

#!!! NOT TESTED
class USPEXStructure:

    # This wrapper tricks USPEX into thinking its submitting structures, when really its just making structures then quitting.
    #!!! In the future, USPEX devs will hopefully have an accessible command to just create structures. This will dramatically improve
    #!!! both the speed of this wrapper as well as the cleaniness of the code.
    # Because this wrapper needs to trick USPEX, it is very slow at calling new_structure. It's much more efficient to trick USPEX a single
    # time and thus make a bunch of structures at once (new_structures). This is because of the overhead of calling USPEX and having it generate
    # input files for a calculation which is never going to actually run. Once USPEX has a convience function for making structures, this can be undone.
    #!!! Also consider reading the .mat files directly so I don't have to waste time generating input folders.
    # https://scipy-cookbook.readthedocs.io/items/Reading_mat_files.html

    # see source: https://uspex-team.org/en/uspex/downloads
    # see tutorials: NONE

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        uspex_python_env="uspex",  # This needs to be a custom python env! It must be Python=2.7 and have Numpy, Scipy, MatPlotLib, ASE, and SpgLib
        uspex_loc="/home/jacksund/USPEX",  # Location where USPEX was installed to -- the command itself doesn't work... I need to figure out what's going on
        conda_loc="/home/jacksund/anaconda3/etc/profile.d/conda.sh",  # this will vary if you didn't install anaconda to your home directory or installed miniconda instead.
        temp_dir="/home/jacksund/Desktop/uspex_tmp",  # this is the temporary directory where I will run uspex
    ):

        self.uspex_python_env = uspex_python_env
        self.temp_dir = temp_dir

        #!!! this is inside the init because not all users will have this installed!
        # see if the user has USPEX installed
        import subprocess

        #!!! what is the best way to see if AIRSS is installed? Check the path?
        output = subprocess.run(
            "USPEX --help",  # command that calls USPEX
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )
        #!!! THIS DOESN'T WORK AT THE MOMENT...
        # if output.returncode != 0:
        #     #!!! I should raise an error in the future
        #     print('You must have USPEX installed to use USPEXStructure!!')
        #     return # exit the function as the script will fail later on otherwise

        #!!! add check that the user is on Linux?

        #!!! add check that the user has a proper python enviornment set up in conda?

        # Format composition in the manner USPEX requests it.
        # This is a list of atomic symvols (for example, MgSiO3 is 'Mg Si O')
        atom_types = " ".join([element.symbol for element in composition])
        # This is a list of non-reduced species count.
        # If I want variable counts, I would use minAt and maxAt settings + the reduced formula, but I don't do that
        num_species = " ".join(
            [str(int(composition[element])) for element in composition]
        )

        # Now let's set all of the other USPEX options
        #!!! consider moving default inputs to the init keyword options
        uspex_options = {
            "calculationType": "300",  # see USPEX docs for more option - for example, set to 200 for 2-D structures
            "symmetries": "2-230",  #!!! how do I make this compatible with spacegroup_options...?
            "fracTopRand": "0.0",  # fraction Topological structures to make #!!! I should keep this as 0 or 1 for clarity within the PyMatDisc code
            "atom_type": atom_types,
            "num_species": num_species,
        }

        # Here we setup the input file to create USPEX structures.
        # Whereever you see some name between brackets {var}, we will replace with the dict above.
        # NUM_STRUCTURES we replace in functions below.
        # Note that the commandExecutable is just a dummy echo command and doesn't do anything.
        # We also set the calc to VASP because we want POSCAR files made for us.
        uspex_input = """
{calculationType} : calculationType

% symmetries
{symmetries}
% endSymmetries

% atomType
{atom_type}
% EndAtomType

% numSpecies
{num_species}
% EndNumSpecies

{fracTopRand} : fracTopRand

NUM_STRUCTURES : initialPopSize

% abinitioCode
1
% ENDabinit

% commandExecutable
echo skip this
% EndExecutable

NUM_STRUCTURES : numParallelCalcs

1 : whichCluster
"""

        # Now format this input string with our options. The only remaining input to set is the number
        # of structures to generate (NUM_STRUCTURES)
        self.uspex_input = uspex_input.format(**uspex_options)

        # In order to have USPEX create structures, it is also going to make input files for VASP.
        # To do this, there needs to be a Specific folder with INCAR_1 and POTCAR_X (X=symbol)
        # Because we aren't really running VASP, these don't need to be legit files. In fact, making them
        # empty is easier on the computer because we don't have to repeated paste large POTCAR files.
        # Let's make those dummy files here.

        # First let's switch to the temp_dir and save the current working dir (cwd) for reference
        import os

        cwd = os.getcwd()
        os.chdir(temp_dir)  #!!! What if dir doesn't exist yet? This will throw an error

        # make the Specifics folder and move into it
        os.mkdir("Specific")
        os.chdir("Specific")

        # Make the INCAR_1 file.
        subprocess.run(
            "echo DUMMY INCAR > INCAR_1",
            shell=True,  # use commands instead of local files
        )

        # Make the POTCAR_X files.
        for element in composition:
            subprocess.run(
                "echo DUMMY POTCAR > POTCAR_{}".format(element.symbol),
                shell=True,  # use commands instead of local files
            )

        # move back to the temp dir
        os.chdir("..")

        # make the Submission folder and move into it
        os.mkdir("Submission")
        os.chdir("Submission")

        # make the submitJob_local.py file
        localsubmit_content = """
from __future__ import with_statement
from __future__ import absolute_import
from subprocess import check_output
import re
import sys
from io import open

def submitJob_local(index, commnadExecutable):
    return 12345 #

if __name__ == u'__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(u'-i', dest=u'index', type=int)
    parser.add_argument(u'-c', dest=u'commnadExecutable', type=unicode)
    args = parser.parse_args()

    jobNumber = submitJob_local(index=args.index, commnadExecutable=args.commnadExecutable)
    print('<CALLRESULT>')
    print(int(jobNumber))
"""
        # write it and close immediately
        file = open("submitJob_local.py", "w")
        file.writelines(localsubmit_content)
        file.close()
        # go back up a directory
        os.chdir("..")

        # The last issue is that USPEX needs a different python enviornment, which we need to access via a script.
        # Let's add a script run_uspex.sh that sets this env for us and then runs uspex.
        submit_content = """
source {conda_loc}
conda activate {uspex_python_env}
export USPEXPATH={uspex_loc}/application/archive/src
export MCRROOT={uspex_loc}
{uspex_loc}/application/archive/USPEX -r
"""
        # write it and close immediately
        file = open("run_uspex.sh", "w")
        file.writelines(
            submit_content.format(
                **{
                    "conda_loc": conda_loc,
                    "uspex_python_env": uspex_python_env,
                    "uspex_loc": uspex_loc,
                }
            )
        )
        file.close()
        # give permissions to the script so we can run it below
        subprocess.run(
            "chmod a+x run_uspex.sh",  #!!! is a+x correct?
            shell=True,  # use commands instead of local files
        )

        # We now have everything except the INPUT.txt file! We will write that and run it below.
        # This is done later because we don't know NUM_STRUCTURES yet

        # switch back to our original working dir
        os.chdir(cwd)

    def new_structures(self, n):

        # See my comments above on why this atypical function exists... (it's much faster than calling USPEX each new struct)

        # First let's switch to the temp_dir and save the current working dir (cwd) for reference
        import os

        cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # make the INPUT.txt file with n as our NUM_STRUCTURES to make
        # write it and close immediately
        file = open("INPUT.txt", "w")
        file.writelines(self.uspex_input.replace("NUM_STRUCTURES", str(n)))
        file.close()

        # now let's have USPEX run and make the structures!
        import subprocess

        output = subprocess.run(
            "bash run_uspex.sh",  #!!! should I pipe the output to a log file?
            shell=True,  # use commands instead of local files
            #!!! comment out the options below if you want USPEX to print to terminal
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )

        # All the structures are put into folders as POSCAR files. The folders are CalcFold1, CalcFold2, ... CalcFold200...
        # Let's iterate through these and pool them into a list
        import shutil  # to remove directories #!!! is there another way to do this?

        structures = []
        for i in range(
            n
        ):  # we can assume all folders are there instead of grabbing os.listdir() for all CalcFold*
            os.chdir(
                "CalcFold{}".format(i + 1)
            )  # the +1 is because we don't want to count from 0
            structure = Structure.from_file(
                "POSCAR"
            )  # convert POSCAR to pymatgen Structure
            structures.append(structure)  # add it to the list
            os.chdir("..")  # move back directory
            shutil.rmtree(
                "CalcFold{}".format(i + 1)
            )  # delete the folder now that we are done with it

        # Do some cleanup and delete all the unneccesary directories that were just made.
        # This sets us up to run new_structures again
        # let's go through the folders first
        rm_dir_list = ["AntiSeeds", "results1", "Seeds", "CalcFoldTemp"]
        for d in rm_dir_list:
            shutil.rmtree(d)
        # Rather than go through a list like with the directories, it's easier
        # to just delete all .mat files because that's what they all are
        subprocess.run(
            "rm *.mat*",
            shell=True,  # use commands instead of local files
        )

        # switch back to our original working dir
        os.chdir(cwd)

        # return the list of pymatgen Structure objects that we've made
        return structures

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # IF YOU WANT TO MAKE MANY STRUCTURES, THIS IS VERY SLOW! Use new_structures(n) instead.

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: While USPEX allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While USPEX allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: While USPEX allows for specifying a spacegroup(s), "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # call the new_structures() function and tell it to create just one structure
        structure = self.new_structures(1)[0]

        return structure


##############################################################################


class CALYPSOStructure:

    # This wrapper runs CALYPSO in 'split mode', where structures are simply created and then no further steps are taken.
    #!!! In the future, CALYPSO devs will hopefully have an accessible command to just create structures. This will dramatically improve
    #!!! both the speed of this wrapper as well as the cleaniness of the code.

    # see source: http://www.calypso.cn/getting-calypso/
    # see tutorials: NONE

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
        calypso_exe_loc="/home/jacksund/Desktop/",  # location of the calypso.x file
        calypso_python_env="uspex",  #!!! CHANGE NAME # This needs to be a custom python env! It must be Python=2.7 and have Numpy, Scipy, MatPlotLib, ASE, and SpgLib
        conda_loc="/home/jacksund/anaconda3/etc/profile.d/conda.sh",  # this will vary if you didn't install anaconda to your home directory or installed miniconda instead.
        temp_dir="/home/jacksund/Desktop/calypso_tmp",  # this is the temporary directory where I will run uspex
    ):
        self.calypso_python_env = calypso_python_env
        self.temp_dir = temp_dir

        #!!! add check that the user is on Linux?

        #!!! add check that the user has a proper python enviornment set up in conda?

        #!!! Because of bug with calypso's poscar files, I need to save this
        self.comp = " ".join([element.symbol for element in composition])

        # Now let's set all of the USPEX options and format them the way they'd like
        #!!! consider moving default inputs to the init keyword options
        # There are many  more options (such as for 2D materials) that can be added
        calypso_options = {
            "NumberOfSpecies": len(composition),  # number of unique elements
            "NameOfAtoms": " ".join(
                [element.symbol for element in composition]
            ),  # This is a list of atomic symvols (for example, MgSiO3 is 'Mg Si O')
            "NumberOfAtoms": " ".join(
                [
                    str(int(composition[element]))
                    for element in composition.reduced_composition
                ]
            ),  # This is a list of reduced species count
            "NumberOfFormula": int(
                composition.num_atoms / composition.reduced_composition.num_atoms
            ),  # factor of formula unit -- for example Mg3Si3O9 would have 3 (vs MgSiO3)
        }

        #!!! CALYPSO's auto volume prediction doesn't look to work very well.
        #!!! It's either that, or the distance checks are too strict.
        # Therefore, let's predict volume on our own and input it.
        from pymatdisc.core.estimate import estimate_volume

        volume = estimate_volume(composition, packing_factor=2)
        calypso_options.update({"Volume": volume})

        # CALYPSO says they have a default value for distances, but it doesn't look like they work.
        # So I am going to end up making a distance matrix here.
        from pymatdisc.core.estimate import distance_matrix

        dm = distance_matrix(composition)
        dm_str = ""
        for row in dm:
            for val in row:
                dm_str += str(val) + " "
            dm_str += "\n"
        dm_str = dm_str[:-2]  # remove the final \n
        calypso_options.update({"DistanceOfIon": dm_str})

        # Here we setup the input file to create CALYPSO structures.
        # Whereever you see some name between brackets {var}, we will replace with the dict above.
        # NUM_STRUCTURES we replace in functions below.
        # Note NumberOfFormula is input twice becuase we want a fixed min/max #!!! change this in the future...?
        calypso_input = """
NumberOfSpecies = {NumberOfSpecies}
NameOfAtoms = {NameOfAtoms}
NumberOfAtoms = {NumberOfAtoms}
NumberOfFormula = {NumberOfFormula} {NumberOfFormula}
PopSize = NUM_STRUCTURES
Command = echo SKIP THIS
Split = T
Volume = {Volume}
@DistanceOfIon
{DistanceOfIon}
@End
"""

        # Now format this input string with our options. The only remaining input to set is the number
        # of structures to generate (NUM_STRUCTURES)
        self.calypso_input = calypso_input.format(**calypso_options)

        # In order to have CALYPSO create structures, we need the calypso.x file copied into our directory

        # First let's switch to the temp_dir and save the current working dir (cwd) for reference
        import os

        cwd = os.getcwd()
        os.chdir(temp_dir)  #!!! What if dir doesn't exist yet? This will throw an error

        # Copy the calypso.x file into this directory
        import subprocess

        subprocess.run(
            "cp {}/calypso.x {}/".format(calypso_exe_loc, temp_dir),
            shell=True,  # use commands instead of local files
        )

        # The last issue is that CALYPSO needs a different python enviornment, which we need to access via a script.
        # Let's add a script run_uspex.sh that sets this env for us and then runs uspex.
        submit_content = """
source {conda_loc}
conda activate {calypso_python_env}
./calypso.x
"""
        # write it and close immediately
        file = open("run_calypso.sh", "w")
        file.writelines(
            submit_content.format(
                **{"conda_loc": conda_loc, "calypso_python_env": calypso_python_env}
            )
        )
        file.close()
        # give permissions to the script so we can run it below
        subprocess.run(
            "chmod a+x run_calypso.sh",  #!!! is a+x correct?
            shell=True,  # use commands instead of local files
        )

        # We now have everything except the INPUT.txt file! We will write that and run it below.
        # This is done later because we don't know NUM_STRUCTURES yet

        # switch back to our original working dir
        os.chdir(cwd)

    def new_structures(self, n):

        # See my comments above on why this atypical function exists... (it's much faster than calling USPEX each new struct)

        # First let's switch to the temp_dir and save the current working dir (cwd) for reference
        import os

        cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # make the INPUT.txt file with n as our NUM_STRUCTURES to make
        # write it and close immediately
        file = open("input.dat", "w")
        file.writelines(self.calypso_input.replace("NUM_STRUCTURES", str(n)))
        file.close()

        # now let's have USPEX run and make the structures!
        import subprocess

        subprocess.run(
            "bash run_calypso.sh",  #!!! should I pipe the output to a log file?
            shell=True,  # use commands instead of local files
            #!!! comment out the options below if you want USPEX to print to terminal
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )

        # All the structures are as POSCAR files. The files are POSCAR_1, POSCAR_2, ... POSCAR_n...
        # Let's iterate through these and pool them into a list
        structures = []
        for i in range(
            n
        ):  # we can assume all folders are there instead of grabbing os.listdir() for all CalcFold*
            poscar_name = "POSCAR_{}".format(i + 1)

            #!!! BUG WITH CALYPSO...
            # They don't add the atom types to the POSCAR... wtf
            # I need to do that manually here
            file = open(poscar_name, "r")
            lines = file.readlines()
            file.close()
            file = open(poscar_name, "w")
            lines.insert(5, self.comp + "\n")  # self.comp
            file.writelines(lines)
            file.close()

            # now we can load the POSCAR and add it to our list
            structure = Structure.from_file(
                poscar_name
            )  # convert POSCAR to pymatgen Structure # the +1 is because we don't want to count from 0
            structures.append(structure)  # add it to the list
            os.remove(poscar_name)  # delete the file now that we are done with it

        # Do some cleanup and delete all the unneccesary directories/files that were just made.
        # This sets us up to run new_structures again
        import shutil  # to remove directories #!!! is there another way to do this?

        shutil.rmtree("results")
        # Rather than go through a list like with the directories, it's easier
        # to just delete all .mat files because that's what they all are
        subprocess.run(
            "rm *.py*",
            shell=True,  # use commands instead of local files
        )
        # There's also two more files to remove - POSCAR and step
        subprocess.run(
            "rm POSCAR; rm step",
            shell=True,  # use commands instead of local files
        )

        # switch back to our original working dir
        os.chdir(cwd)

        # return the list of pymatgen Structure objects that we've made
        return structures

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # IF YOU WANT TO MAKE MANY STRUCTURES, THIS IS VERY SLOW! Use new_structures(n) instead.

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: While CALYPSO allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While CALYPSO allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: While CALYPSO allows for specifying a spacegroup(s), "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # call the new_structures() function and tell it to create just one structure
        structure = self.new_structures(1)[0]

        return structure


##############################################################################
