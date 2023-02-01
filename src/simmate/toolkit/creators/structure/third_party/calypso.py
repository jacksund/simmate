# -*- coding: utf-8 -*-

import shutil
import subprocess

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator
from simmate.utilities import get_directory


class CalypsoStructure(StructureCreator):
    """
    Creates structures using the CALYPSO package

    This wrapper runs CALYPSO in 'split mode', where structures are simply
    created and then no further steps are taken.

    In the future, CALYPSO devs will hopefully have an accessible command
    # to just create structures. This will dramatically improve both the speed
    of this wrapper as well as the cleaniness of the code.

    source: http://www.calypso.cn/getting-calypso/


    ## Dev Notes

    For Ubuntu, I downloaded the x64 version of CALYPSO 7.0. Simply uncompress
    the download file and the executable is there. No need for any install.

    The following dependency is needed on ubuntu:
    ``` bash
    sudo apt-get install libomp-dev
    ```

    To generate structures without running any analysis/calcs, I simply need
    to run calypso in split mode:
    ```
    Split = T
    ```

    All the structures are put into POSCAR files named POSCAR_1, POSCAR_2, ... POSCAR_N
    """

    def __init__(
        self,
        composition: Composition,
        # location of the calypso.x file
        command: str = "calypso.x",
    ):
        if not shutil.which(command):
            raise Exception("You must have CALYPSO installed and in the PATH.")

        self.command = command

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
                    str(int(composition.reduced_composition[element]))
                    for element in composition
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

    def create_structures(self, n: int) -> list[Structure]:
        # See my comments above on why this atypical function exists...
        # (it's much faster than calling USPEX each new struct)

        temp_dir = get_directory()  # leave empty to allow parallel

        # make the INPUT.txt file with n as our NUM_STRUCTURES to make
        # write it and close immediately
        input_file = temp_dir / "input.dat"
        with input_file.open("w") as file:
            file.writelines(self.calypso_input.replace("NUM_STRUCTURES", str(n)))

        # now let's have CALYPSO run and make the structures
        subprocess.run(
            self.command,
            shell=True,
            capture_output=True,
            cwd=temp_dir,
        )

        # All the structures are as POSCAR files. The files are
        #   POSCAR_1, POSCAR_2, ... POSCAR_n...
        # Let's iterate through these and pool them into a list
        structures = []
        for poscar_file in temp_dir.iterdir():
            if not poscar_file.stem.startswith("POSCAR_"):
                continue

            # ----------------------------
            # BUG WITH CALYPSO...
            # They don't add the atom types to the POSCAR... wtf
            # I need to do that manually here
            with poscar_file.open("r") as file:
                lines = file.readlines()
            # add the composition line
            lines.insert(5, self.comp + "\n")
            # write the updated file
            with poscar_file.open("w") as file:
                file.writelines(lines)
            # ----------------------------

            # now we can load the POSCAR and add it to our list
            structure = Structure.from_file(poscar_file)
            structures.append(structure)

        # delete the directory
        shutil.rmtree(temp_dir)

        # return the list of pymatgen Structure objects that we've made
        return structures

    def create_structure(self) -> Structure:
        # call the create_structures() function and tell it to create
        # just one structure
        structure = self.create_structures(1)[0]

        return structure


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
