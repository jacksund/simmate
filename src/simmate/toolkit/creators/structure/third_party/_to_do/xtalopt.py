# -*- coding: utf-8 -*-

from numpy.random import choice

from simmate.toolkit import Structure

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

        volume = composition.volume_estimate()
        # set the limits on volume (should I do this?)
        self.min_volume = volume * 0.5
        self.max_volume = volume * 1.5
        # let's set the minimum to the smallest radii
        min_vector = min(composition.radii_estimate())
        # let's set the maximum to volume**0.8 #!!! This is a huge range and I should test this in the future
        max_vector = volume**0.8
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
