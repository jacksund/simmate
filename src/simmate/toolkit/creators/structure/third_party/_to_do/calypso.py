# -*- coding: utf-8 -*-

from simmate.toolkit import Structure

# TODO: Maybe make a CALYPSO calculator

#!!! NOT TESTED
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
