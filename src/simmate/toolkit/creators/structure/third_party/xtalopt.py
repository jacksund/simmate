# -*- coding: utf-8 -*-

import logging
import shutil
import subprocess

from numpy.random import choice

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator
from simmate.utilities import get_directory

# This input is based off of...
#   https://github.com/xtalopt/randSpg/blob/master/sample/randSpg.in
INPUT_TEMPLATE = """
First line is a comment line
composition            = {composition}
spacegroups             = {spacegroup}
forceMostGeneralWyckPos = False

#                           a,    b,    c, alpha,  beta, gamma
latticeMins            = {lattice_min}
latticeMaxes           = {lattice_max}
minVolume              = {volume_min}
maxVolume              = {volume_max}

# how many crystals of each spg to generate
numOfEachSpgToGenerate = 1

maxAttempts            = 1000
setMinRadii            = 0.4
scalingFactor          = 0.5
outputDir              = randSpgOut
verbosity              = r
"""


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
    sudo snap install cmake --classic;
    ```

    Download the randSpg files from github and extract them to your desktop

    Now we can run their compiling commands (starting in the main randSpg directory):
    ```
    mkdir build;
    cd build;
    cmake ..;
    make -j3;
    ```

    Copy the build/randSpg file to a separate /bin folder

    Add the following to the bottom of ~/.bashrc
    ```
    export PATH=/home/jacksund/Documents/github/randSpg/bin/:$PATH
    ```

    -------------------
    BUG: This section for python bindings is broken. Try without python bindings
    Next we need to have a python environment with pybind11 installed (this
    is just for making the files, you can use a different env after):
    ```
    conda create -n randspg -c conda-forge python=3.7
    conda activate randspg
    conda install -n randspg -c conda-forge pybind11
    ```
    Edit the CMakeLists.txt file, where we want to turn BUILD_PYTHON_BINDINGS
    from OFF to ON. (note - do this via the command line with nano)
    (after compile)
    Inside of the build/python folder, there is a file with a really long name
    -- looks like pyrandspg.cython......so. This is the file we will import
    the python module from.
    Move that file to your 'GitHub' directory (or wherever you can import from).
    Move the build directory whereever you'd like to store the installation.
    I put it in my home folder and renamed it from build to randSpg
    We can delete the rest.
    -------------------
    """

    def __init__(
        self,
        composition: Composition,
        command: str = "randSpg",  # /home/jacksund/Documents/github/randSpg/build/randSpg
        spacegroup_include: list[int] = range(1, 231),
        spacegroup_exclude: list[int] = [],
    ):
        # check that the command exists
        if not shutil.which(command):
            raise Exception("randSpg must be installed and available in the PATH")
        self.command = command

        # the input file wants the formula without spaces
        self.composition = str(composition).replace(" ", "")

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
        self.volume_min = volume * 0.5
        self.volume_max = volume * 1.5
        # let's set the minimum to the smallest radii
        min_vector = float(min(composition.radii_estimate()))
        # let's set the maximum to volume**0.8
        max_vector = volume**0.8
        # a,b,c,alpha,beta,gamma
        self.lattice_min = (3 * (str(min_vector) + ", ")) + "60.0, 60.0, 60.0"
        self.lattice_max = (3 * (str(max_vector) + ", ")) + "120.0, 120.0, 120.0"

    def create_structure(self, spacegroup: int = None) -> Structure:
        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible
        # with the vector_generator built
        if not spacegroup:
            # randomly select a symmetry system
            spacegroup = choice(self.spacegroup_options)

        temp_directory = get_directory()  # keep random name to all parallel runs

        input_file = temp_directory / "random.in"
        with input_file.open("w") as file:
            content = INPUT_TEMPLATE.format(
                composition=self.composition,
                spacegroup=spacegroup,
                lattice_min=self.lattice_min,
                lattice_max=self.lattice_max,
                volume_min=self.volume_min,
                volume_max=self.volume_max,
            )
            file.write(content)

        # call randSpg
        subprocess.run(
            f"{self.command} {str(input_file)}",
            cwd=temp_directory,
            shell=True,
            capture_output=True,
        )

        # BUG: even failed runs return a successful error code
        # if process.returncode == 1:

        output_dir = temp_directory / "randSpgOut"
        poscare_filename = output_dir / "POSCAR"

        # there should only be one structure for now. So this will really
        # just load one file.
        # The names of the output POSCARs are <composition>_<spg>-<index>
        structure = False
        for file in output_dir.iterdir():
            file.rename(poscare_filename)
            structure = Structure.from_file(poscare_filename)

        # delete the temporary directory
        shutil.rmtree(temp_directory)

        if not structure:
            logging.info(
                f"Removed spacegroup {spacegroup} from options due to failure. "
                "This will not be selected moving forward."
            )
            self.spacegroup_options.remove(spacegroup)

        return structure

    # -------------------------------------------------------------------------
    # Broken methods that might be reused if BUGs are fixed by the randSpg team.
    # Though this is unlikely because they haven't updated their repo since 2017
    # -------------------------------------------------------------------------

    def _old_init_(
        self,
        composition: Composition,
        spacegroup_include: list[int] = range(1, 231),
        spacegroup_exclude: list[int] = [],
    ):
        # BUG: python binding are broken for randSpg
        raise Exception(
            "python binding are broken for randSpg. This method is kept only "
            "in case they are fixed by the XtalOpt team."
        )

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
        self.volume_max = volume * 1.5
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

    def _create_structure_old(self, spacegroup: int = None) -> Structure:
        # BUG: python binding are broken for randSpg
        raise Exception(
            "python binding are broken for randSpg. This method is kept only "
            "in case they are fixed by the XtalOpt team."
        )

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
        input_settings.maxVolume = self.volume_max

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
