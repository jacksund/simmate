# -*- coding: utf-8 -*-

from simmate.toolkit import Structure

# TODO: Maybe make an USPEX calculator

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
