# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator

# Here we setup the input file to create CALYPSO structures.
# Note NumberOfFormula is input twice becuase we want a fixed min/max
INPUT_TEMPLATE = """
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

# The last issue is that CALYPSO needs a different python enviornment,
# which we need to access via a script.
# Let's add a script run_uspex.sh that sets this env for us and then runs uspex.
SUBMIT_TEMPLATE = """
source {conda_loc}
conda activate {calypso_python_env}
./calypso.x
"""


class CalypsoStructure(StructureCreator):
    """
    Creates structures using the CALYPSO package

    This wrapper runs CALYPSO in 'split mode', where structures are simply
    created and then no further steps are taken.

    In the future, CALYPSO devs will hopefully have an accessible command
    # to just create structures. This will dramatically improve both the speed
    of this wrapper as well as the cleaniness of the code.

    source: http://www.calypso.cn/getting-calypso/
    """

    def __init__(
        self,
        composition: Composition,
        # location of the calypso.x file
        calypso_exe_loc="/home/jacksund/Desktop/",
        # This needs to be a custom python env! It must be Python=2.7 and have
        # Numpy, Scipy, MatPlotLib, ASE, and SpgLib
        calypso_python_env="uspex",
        # this will vary if you didn't install anaconda to your home
        # directory or installed miniconda instead.
        conda_loc="/home/jacksund/anaconda3/etc/profile.d/conda.sh",
        # # this is the temporary directory where I will run calypso
        temp_dir="/home/jacksund/Desktop/calypso_tmp",
    ):
        self.calypso_python_env = calypso_python_env
        self.temp_dir = temp_dir

        # TODO
        # add check that the user is on Linux
        # add check that the user has a proper python enviornment set up in conda

        # Because of bug with calypso's poscar files, I need to save this
        self.comp = " ".join([element.symbol for element in composition])

        # set all of the USPEX options and format them the way they'd like
        # There are many  more options (such as for 2D materials) that can be added
        calypso_options = {
            # number of unique elements
            "NumberOfSpecies": len(composition),
            # This is a list of atomic symvols (for example, MgSiO3 is 'Mg Si O')
            "NameOfAtoms": " ".join([element.symbol for element in composition]),
            # This is a list of reduced species count
            "NumberOfAtoms": " ".join(
                [
                    str(int(composition[element]))
                    for element in composition.reduced_composition
                ]
            ),
            # factor of formula unit -- for example Mg3Si3O9 would have 3 (vs MgSiO3)
            "NumberOfFormula": int(
                composition.num_atoms / composition.reduced_composition.num_atoms
            ),
        }

        # CALYPSO's auto volume prediction doesn't look to work very well.
        # It's either that, or the distance checks are too strict.
        # Therefore, let's predict volume on our own and input it.
        volume = composition.volume_estimate(packing_factor=2)
        calypso_options.update({"Volume": volume})

        # CALYPSO says they have a default value for distances, but it doesn't
        # look like they work. So I am going to end up making a distance
        # matrix here.
        dm = composition.distance_matrix_estimate()
        dm_str = ""
        for row in dm:
            for val in row:
                dm_str += str(val) + " "
            dm_str += "\n"
        dm_str = dm_str[:-2]  # remove the final \n
        calypso_options.update({"DistanceOfIon": dm_str})

        # Now format this input string with our options. The only remaining
        # input to set is the number of structures to generate (NUM_STRUCTURES)
        self.calypso_input = INPUT_TEMPLATE.format(**calypso_options)

        # In order to have CALYPSO create structures, we need the calypso.x
        # file copied into our directory

        # First let's switch to the temp_dir and save the current working
        # dir (cwd) for reference
        cwd = os.getcwd()
        os.chdir(temp_dir)

        # Copy the calypso.x file into this directory
        subprocess.run(
            "cp {}/calypso.x {}/".format(calypso_exe_loc, temp_dir),
            shell=True,  # use commands instead of local files
        )

        # write it and close immediately
        with open("run_calypso.sh", "w") as file:
            file.writelines(
                SUBMIT_TEMPLATE.format(
                    **{
                        "conda_loc": conda_loc,
                        "calypso_python_env": calypso_python_env,
                    }
                )
            )

        # give permissions to the script so we can run it below
        subprocess.run(
            "chmod a+x run_calypso.sh",
            shell=True,
        )

        # We now have everything except the INPUT.txt file! We will write that
        # and run it below.
        # This is done later because we don't know NUM_STRUCTURES yet

        # switch back to our original working dir
        os.chdir(cwd)

    def create_structures(self, n: int) -> list[Structure]:

        # See my comments above on why this atypical function exists...
        # (it's much faster than calling USPEX each new struct)

        # First let's switch to the temp_dir and save the current working dir
        # (cwd) for reference
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
            "bash run_calypso.sh",
            shell=True,
            capture_output=True,
            text=True,
        )

        # All the structures are as POSCAR files. The files are
        #   POSCAR_1, POSCAR_2, ... POSCAR_n...
        # Let's iterate through these and pool them into a list
        structures = []
        # we can assume all folders are there instead of grabbing
        # os.listdir() for all CalcFold*
        for i in range(n):
            poscar_name = "POSCAR_{}".format(i + 1)

            #!!! BUG WITH CALYPSO...
            # They don't add the atom types to the POSCAR... wtf
            # I need to do that manually here
            with open(poscar_name, "r") as file:
                lines = file.readlines()

            # add the composition line
            lines.insert(5, self.comp + "\n")

            # write the updated file
            with open(poscar_name, "w") as file:
                file.writelines(lines)

            # now we can load the POSCAR and add it to our list
            structure = Structure.from_file(poscar_name)
            structures.append(structure)

            # delete the file now that we are done with it
            os.remove(poscar_name)

        # Do some cleanup and delete all the unneccesary directories/files 
        # that were just made.
        # This sets us up to run new_structures again
        shutil.rmtree("results")
        # Rather than go through a list like with the directories, it's easier
        # to just delete all .mat files because that's what they all are
        subprocess.run("rm *.py*", shell=True)
        # There's also two more files to remove - POSCAR and step
        subprocess.run("rm POSCAR; rm step", shell=True)

        # switch back to our original working dir
        os.chdir(cwd)

        # return the list of pymatgen Structure objects that we've made
        return structures

    def create_structure(self) -> Structure:

        # call the create_structures() function and tell it to create 
        # just one structure
        structure = self.create_structures(1)[0]

        return structure
