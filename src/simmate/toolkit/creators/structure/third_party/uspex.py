# -*- coding: utf-8 -*-

import shutil
import subprocess
import time

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator
from simmate.utilities import get_directory


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
        command: str = "uspex",
        command_build: str = "buildcell",
        # This needs to be a custom python env! It must be Python=2.7 and
        # have Numpy, Scipy, MatPlotLib, ASE, and SpgLib
        conda_env: str = "uspex_env",
    ):
        self.composition = composition

        # BUG: in separate env right now
        # check that the command exists
        if not shutil.which(command_build):  # and not shutil.which(command)
            raise Exception(
                "You must have USPEX installed and the uspex & buildcell "
                "commands in your PATH."
            )

        self.command = command

        self.conda_env = conda_env

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
            "symmetries": "1-230",
            "fracTopRand": "0.0",  # fraction Topological structures to make
            "atom_type": atom_types,
            "num_species": num_species,
        }

        # Now format this input string with our options. The only remaining
        # input to set is the number of structures to generate (NUM_STRUCTURES)
        self.uspex_input = INPUT_TEMPLATE.format(**uspex_options)

    def create_structures(self, n: int, sleep_step: float = 5) -> list[Structure]:
        # In order to have USPEX create structures, it is also going to make
        # input files for VASP. To do this, there needs to be a Specific folder
        # with INCAR_1 and POTCAR_X (X=symbol). Because we aren't really
        # running VASP, these don't need to be legit files. In fact, making them
        # empty is easier on the computer because we don't have to repeated
        # paste large POTCAR files. Let's make those dummy files here.

        temp_dir = get_directory()

        # make the Specifics folder and move into it
        specific_dir = get_directory(temp_dir / "Specific")

        # Make the INCAR_1 file.
        incar_1 = specific_dir / "INCAR_1"
        with incar_1.open("w") as file:
            file.write("DUMMY INCAR")

        # Make the POTCAR_X files.
        for element in self.composition:
            potcar = specific_dir / f"POTCAR_{element.symbol}"
            with potcar.open("w") as file:
                file.write("DUMMY POTCAR")

        # make the Submission folder and move into it
        specific_dir = get_directory(temp_dir / "Submission")

        # make the submitJob_local.py file
        submit_local_file = specific_dir / "submitJob_local.py"
        with submit_local_file.open("w") as file:
            file.writelines(SUBMIT_SCRIPT)

        # write it and close immediately
        submit_script = temp_dir / "run_uspex.sh"
        with submit_script.open("w") as file:
            content = SUBMIT_TEMPLATE.format(
                conda_env=self.conda_env,
                command=self.command,
            )
            file.writelines(content)

        # give permissions to the script so we can run it below
        subprocess.run(
            "chmod a+x run_uspex.sh",
            shell=True,
            cwd=temp_dir,
        )

        # We now have everything except the INPUT.txt file! We will write
        # that and run it below.
        # This is done later because we don't know NUM_STRUCTURES yet

        # make the INPUT.txt file with n as our NUM_STRUCTURES to make
        # write it and close immediately
        input_file = temp_dir / "input.uspex"
        with input_file.open("w") as file:
            content = self.uspex_input.replace("NUM_STRUCTURES", str(n))
            file.writelines(content)

        # now let's have USPEX run and make the structures
        process = subprocess.Popen(
            "bash run_uspex.sh",
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=temp_dir,
        )

        # check if the shelltasks is complete. poll will return 0
        # when it's done, in which case we break the loop
        log_file = temp_dir / "log"

        is_done = False
        while not is_done:
            if log_file.exists():
                with log_file.open("r") as file:
                    lines = file.readlines()
                for line in lines:
                    if "RuntimeError" in line:
                        is_done = True
                        process.terminate()
                        break
            time.sleep(sleep_step)

        # All the structures are put into folders as POSCAR files. The folders
        # are CalcFold1, CalcFold2, ... CalcFold200...
        # Let's iterate through these and pool them into a list to
        # remove directories
        structures = []

        for folder in temp_dir.iterdir():
            if not folder.is_dir() or not folder.stem.startswith("CalcFold"):
                continue

            poscar_file = folder / "POSCAR"
            structure = Structure.from_file(poscar_file)
            structures.append(structure)

        # delete the directory
        shutil.rmtree(temp_dir, ignore_errors=True)

        # return the list of pymatgen Structure objects that we've made
        return structures

    def create_structure(self) -> Structure:
        # call the new_structures() function and tell it to create
        # just one structure
        structure = self.create_structures(1)[0]

        return structure


# -----------------------------------------------------------------------------
# Below are templates for writing USPEX input files
# -----------------------------------------------------------------------------

# Here we setup the input file to create USPEX structures.
# Note that the commandExecutable is just a dummy echo command and doesn't
# do anything.
# We also set the calc to VASP because we want POSCAR files made for us.
INPUT_TEMPLATE = """
{{
    optimizer: {{
        type: GlobalOptimizer
        target: {{
            type: Atomistic
            compositionSpace: {{symbols: [{atom_type}]
                               blocks: [[{num_species}]]}}
            randSym: {{nsym: '{symmetries}'}}
        }}
        optType: enthalpy
        selection: {{
            type: USPEXClassic
            initialPopSize: NUM_STRUCTURES
            fractions: {{
                randSym: (0.05 1.0 1.0)
                randTop: (0.05 1.0 {fracTopRand})
            }}
            popSize: 100
            bestFrac: 0.6
            optType: (aging enthalpy)
        }}
    }}
    stages: [vasp1]
    numParallelCalcs: NUM_STRUCTURES
    numGenerations: 1
    stopCrit: 1
}}

#define vasp1
{{type : vasp, commandExecutable : 'echo DUMMY', kresol: 0.13}}
"""


SUBMIT_SCRIPT = """
from __future__ import with_statement
from __future__ import absolute_import
from subprocess import check_output
import re
import sys
from io import open

# WE DELETED THE ENITRE FUNCTION HERE AND NOW RETURN A RANDOM NUMBER
# Note, the number is just a JobID reference that we will never use
def submitJob_local(index, commnadExecutable):
    return 12345 #

if __name__ == u'__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(u'-i', dest=u'index', type=int)
    parser.add_argument(u'-c', dest=u'commnadExecutable', type=unicode)
    args = parser.parse_args()

    jobNumber = submitJob_local(
        index=args.index, 
        commnadExecutable=args.commnadExecutable,
    )
    print('<CALLRESULT>')
    print(int(jobNumber))
"""

# The last issue is that USPEX needs a different python enviornment,
# which we need to access via a script.
# Let's add a script run_uspex.sh that sets this env for us and
# then runs uspex.
# https://stackoverflow.com/questions/34534513/
SUBMIT_TEMPLATE = """
eval "$(conda shell.bash hook)"
conda activate {conda_env}
{command} -r
"""
