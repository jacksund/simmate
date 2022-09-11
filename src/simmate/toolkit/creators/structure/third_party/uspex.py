# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator

# Here we setup the input file to create USPEX structures.
# Note that the commandExecutable is just a dummy echo command and doesn't
# do anything.
# We also set the calc to VASP because we want POSCAR files made for us.
INPUT_TEMPLATE = """
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

SUBMIT_SCRIPT = """
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

# The last issue is that USPEX needs a different python enviornment,
# which we need to access via a script.
# Let's add a script run_uspex.sh that sets this env for us and
# then runs uspex.
SUBMIT_TEMPLATE = """
source {conda_loc}
conda activate {uspex_python_env}
export USPEXPATH={uspex_loc}/application/archive/src
export MCRROOT={uspex_loc}
{uspex_loc}/application/archive/USPEX -r
"""


class UspexStructure(StructureCreator):
    """
    Creates random structures using USPEX.

    This wrapper tricks USPEX into thinking its submitting structures, when
    really its just making structures then quitting.

    Because this wrapper needs to trick USPEX, it is very slow at calling
    new_structure. It's much more efficient to trick USPEX a single time and
    thus make a bunch of structures at once (new_structures). This is because
    of the overhead of calling USPEX and having it generate input files for a
    calculation which is never going to actually run. Once USPEX has a convience
    function for making structures, this can be undone.

    see source: https://uspex-team.org/en/uspex/downloads
    """

    # In the future, USPEX devs will hopefully have an accessible command to
    # just create structures. This will dramatically improve
    # both the speed of this wrapper as well as the cleaniness of the code.

    # Also consider reading the .mat files directly so I don't have to waste
    # time generating input folders.
    #   https://scipy-cookbook.readthedocs.io/items/Reading_mat_files.html

    def __init__(
        self,
        composition: Composition,
        # This needs to be a custom python env! It must be Python=2.7 and
        # have Numpy, Scipy, MatPlotLib, ASE, and SpgLib
        uspex_python_env: str = "uspex",
        # # Location where USPEX was installed to -- the command itself
        # doesn't work... I need to figure out what's going on
        uspex_loc: str = "/home/jacksund/USPEX",
        # # this will vary if you didn't install anaconda to your home
        # directory or installed miniconda instead.
        conda_loc: str = "/home/jacksund/anaconda3/etc/profile.d/conda.sh",
        # # this is the temporary directory where I will run uspex
        temp_dir: str = "/home/jacksund/Desktop/uspex_tmp",
    ):

        self.uspex_python_env = uspex_python_env
        self.temp_dir = temp_dir

        # TODO: check uspex is installed
        # output = subprocess.run(
        #     "USPEX --help",
        #     shell=True,
        #     capture_output=True,
        #     text=True,  # convert output from bytes to string
        # )

        # Format composition in the manner USPEX requests it.
        # This is a list of atomic symvols (for example, MgSiO3 is 'Mg Si O')
        atom_types = " ".join([element.symbol for element in composition])
        # This is a list of non-reduced species count.
        # If I want variable counts, I would use minAt and maxAt settings
        # + the reduced formula, but I don't do that
        num_species = " ".join(
            [str(int(composition[element])) for element in composition]
        )

        # Now let's set all of the other USPEX options
        uspex_options = {
            # see USPEX docs for more option - for example, set to 200
            # for 2-D structures
            "calculationType": "300",
            "symmetries": "2-230",
            "fracTopRand": "0.0",  # fraction Topological structures to make
            "atom_type": atom_types,
            "num_species": num_species,
        }

        # Now format this input string with our options. The only remaining
        # input to set is the number of structures to generate (NUM_STRUCTURES)
        self.uspex_input = INPUT_TEMPLATE.format(**uspex_options)

        # In order to have USPEX create structures, it is also going to make
        # input files for VASP. To do this, there needs to be a Specific folder
        # with INCAR_1 and POTCAR_X (X=symbol). Because we aren't really
        # running VASP, these don't need to be legit files. In fact, making them
        # empty is easier on the computer because we don't have to repeated
        # paste large POTCAR files. Let's make those dummy files here.

        # First let's switch to the temp_dir and save the current working
        # dir (cwd) for reference
        cwd = os.getcwd()
        os.chdir(temp_dir)

        # make the Specifics folder and move into it
        os.mkdir("Specific")
        os.chdir("Specific")

        # Make the INCAR_1 file.
        subprocess.run("echo DUMMY INCAR > INCAR_1", shell=True)

        # Make the POTCAR_X files.
        for element in composition:
            subprocess.run(
                f"echo DUMMY POTCAR > POTCAR_{element.symbol}",
                shell=True,
            )

        # move back to the temp dir
        os.chdir("..")

        # make the Submission folder and move into it
        os.mkdir("Submission")
        os.chdir("Submission")

        # make the submitJob_local.py file
        with open("submitJob_local.py", "w") as file:
            file.writelines(SUBMIT_SCRIPT)

        # go back up a directory
        os.chdir("..")

        # write it and close immediately
        with open("run_uspex.sh", "w") as file:
            file.writelines(
                SUBMIT_TEMPLATE.format(
                    **{
                        "conda_loc": conda_loc,
                        "uspex_python_env": uspex_python_env,
                        "uspex_loc": uspex_loc,
                    }
                )
            )
        # give permissions to the script so we can run it below
        subprocess.run("chmod a+x run_uspex.sh", shell=True)

        # We now have everything except the INPUT.txt file! We will write
        # that and run it below.
        # This is done later because we don't know NUM_STRUCTURES yet

        # switch back to our original working dir
        os.chdir(cwd)

    def new_structures(self, n: int) -> list[Structure]:

        # See my comments above on why this atypical function exists...
        # (it's much faster than calling USPEX each new struct)

        # First let's switch to the temp_dir and save the current working dir
        # (cwd) for reference

        cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # make the INPUT.txt file with n as our NUM_STRUCTURES to make
        # write it and close immediately
        file = open("INPUT.txt", "w")
        file.writelines(self.uspex_input.replace("NUM_STRUCTURES", str(n)))
        file.close()

        # now let's have USPEX run and make the structures
        subprocess.run(
            "bash run_uspex.sh",
            shell=True,
            capture_output=True,
            text=True,
        )

        # All the structures are put into folders as POSCAR files. The folders
        # are CalcFold1, CalcFold2, ... CalcFold200...
        # Let's iterate through these and pool them into a list to
        # remove directories
        structures = []
        # we can assume all folders are there instead of grabbing os.listdir()
        # for all CalcFold*
        for i in range(n):
            os.chdir("CalcFold{}".format(i + 1))
            structure = Structure.from_file("POSCAR")
            structures.append(structure)  # add it to the list
            os.chdir("..")  # move back directory
            # delete the folder now that we are done with it
            shutil.rmtree("CalcFold{}".format(i + 1))

        # Do some cleanup and delete all the unneccesary directories that
        # were just made.
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

    def new_structure(self) -> Structure:

        # call the new_structures() function and tell it to create
        # just one structure
        structure = self.new_structures(1)[0]

        return structure
