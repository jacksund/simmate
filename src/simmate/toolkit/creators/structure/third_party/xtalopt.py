# -*- coding: utf-8 -*-

from numpy.random import choice

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator


class XtaloptStructure(StructureCreator):
    """
    Uses randSpg (from the XtalOpt team) to create structures.

    see source: https://github.com/xtalopt/randSpg
    see tutorials: https://github.com/zbwang/randSpg/


    ## DEV NOTES
    We actually just want the submodule that creates structures for XtalOpt --
    this is RandSpg
    To install - https://github.com/xtalopt/randSpg
    I make this on Ubuntu using their directions (plus a little extra setup).

    First we need cmake installed. I had this already, but if it isn't there
    for you already use this command:
    ```
    snap install cmake --classic;
    ```

    Next we need to have a python environment with pybind11 installed (this
    is just for making the files, you can use a different env after):
    ```
    conda create -n randspg python=3.7;
    conda activate randspg;
    conda install -n randspg -c conda-forge pybind11;
    ```

    Download the randSpg files from github and extract them to your desktop
    Edit the CMakeLists.txt file, where we want to turn BUILD_PYTHON_BINDINGS
    from OFF to ON. (note - do this via the command line with nano)
    Now we can run their compiling commands (starting in the main randSpg directory):
    ```
    mkdir build;
    cd build;
    cmake ..;
    make -j3;
    ```

    Inside of the build/python folder, there is a file with a really long name
    -- looks like pyrandspg.cython......so. This is the file we will import
    the python module from.
    Move that file to your 'GitHub' directory (or wherever you can import from).
    Move the build directory whereever you'd like to store the installation.
    I put it in my home folder and renamed it from build to randSpg
    We can delete the rest.
    """

    def __init__(
        self,
        composition: Composition,
        spacegroup_include: list[int] = range(1, 231),
        spacegroup_exclude: list[int] = [],
    ):

        try:
            from pyrandspg import LatticeStruct, RandSpg, RandSpgInput

            # save for reference later
            self.RandSpgInput = RandSpgInput
            self.RandSpg = RandSpg
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "You must have XtalOpt installed to use XtalOptStructure. "
                " More specifically, this wrapper uses the randSpg submodule "
                "of XtalOpt and the python bindings made for it (pyrandspg)."
            )

        # make a list of spacegroups that we are allowed to choose from
        self.spacegroup_options = [
            sg for sg in spacegroup_include if sg not in spacegroup_exclude
        ]

        # first establish the min/max values for the lattice vectors and angles
        #!!! change these to user inputs in the future
        # There's no fixed volume setting for XtalOpt so I need to set a
        # minVol, maxVol, and vector limits
        volume = composition.volume_estimate()
        # set the limits on volume (should I do this?)
        self.min_volume = volume * 0.5
        self.max_volume = volume * 1.5
        # let's set the minimum to the smallest radii
        min_vector = min(composition.radii_estimate())
        # let's set the maximum to volume**0.8
        max_vector = volume**0.8
        self.lattice_min = LatticeStruct(
            min_vector, min_vector, min_vector, 60.0, 60.0, 60.0
        )  # a,b,c,alpha,beta,gamma
        self.lattice_max = LatticeStruct(
            max_vector, max_vector, max_vector, 120.0, 120.0, 120.0
        )

        # Format composition in the manner randspg wants it.
        # This is a list of atomic numbers
        #   (for example, MgSiO3 is [12, 14, 8, 8, 8])
        self.atomic_nums = [
            element.number
            for element in composition
            for x in range(int(composition[element]))
        ]

    def create_structure(self, spacegroup: int = None) -> Structure:

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible
        # with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        # now make the new structure using
        #   gasp.organism_creators.RandomOrganismCreator
        # establish input settings
        input_settings = self.RandSpgInput(
            spacegroup,
            self.atomic_nums,
            self.lattice_min,
            self.lattice_max,
        )
        # because I can't use keywords in the input above, I need to set these
        input_settings.forceMostGeneralWyckPos = False
        input_settings.maxAttempts = 1000  # default=100 but leads to many failures
        input_settings.minVolume = self.min_volume
        input_settings.maxVolume = self.max_volume

        # TODO:
        # other options that I can add (I should have these in init above)
        # see https://github.com/xtalopt/randSpg/blob/master/python/pyrandspg.cpp
        #   IADScalingFactor
        #   minRadius
        #   manualAtomicRadii
        #   customMinIADs
        #   minVolume
        #   maxVolume
        #   forcedWyckAssignments
        #   verbosity
        #   maxAttempts
        #   forceMostGeneralWyckPos

        structure_randspg = self.RandSpg.randSpgCrystal(input_settings)

        # Even if the generation fails, an object is still returned.
        # We therefore need to catch failed structures by looking at the
        # numAtoms. If that indicates there are zero atoms, then we know
        # the creation failed
        if structure_randspg.numAtoms() == 0:
            # failed to make a structure
            return False

        # convert the randspg object to pymatgen Structure
        poscar_str = structure_randspg.getPOSCARString()
        structure = Structure.from_str(poscar_str, "poscar")

        return structure
