# -*- coding: utf-8 -*-

import os
import subprocess

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator


class AirssStructure(StructureCreator):
    """
    Creates structures using the AIRSS software package.

    source: https://www.mtg.msm.cam.ac.uk/Codes/AIRSS
    tutorials: https://airss-docs.github.io/
    installation: https://airss-docs.github.io/getting-started/installation/

    Dev Notes:

    To install - https://airss-docs.github.io/getting-started/installation/
    It looks like we would only want their structure generation method, which
    is carried out via the buildcell script. They have a full page on its
    use: https://airss-docs.github.io/technical-reference/buildcell-manual/
    We first need to make a *.cell file with all of the inputs. The inputs are
    listed on their "Buildcell Manual" page, but the documentation is largely
    incomplete. After going through their examples, here's how I think we can
    make the *.cell file:
    ```
    #VARVOL=35
    #SPECIES=Si%NUM=1,O%NUM=2
    #MINSEP=1.0 Si-Si=3.00 Si-O=1.60 O-O=2.58
    ```

    Then to create a cif from these settings, we use the AIRSS structure
    converter (cabal):
    ```
    buildcell < test.cell | cabal cell cif > test.cif
    ```

    If a structure can't be made, this will continue indefinitely
    (MAXTIME doesnt fix this for some reason).
    """

    def __init__(self, composition: Composition):

        # see if the user has AIRSS installed
        output = subprocess.run(
            "airss.pl",  # command that calls AIRSS
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )
        if output.returncode == 1:
            raise Exception(
                "You must have AIRSS installed to use AirssStructure."
                "See https://airss-docs.github.io/getting-started/installation/"
            )

        # to setup the AIRSS creator, we need to make a *.cell file that
        # for example, a SiO2 file will look like... (NOTE - the # symbols
        # should be included in the file):
        # VARVOL=35
        # SPECIES=Si%NUM=1,O%NUM=2
        # MINSEP=1.0 Si-Si=3.00 Si-O=1.60 O-O=2.58

        # lets make this file and name it after the composition
        self.cell_filename = (
            composition.formula.replace(" ", "") + ".cell"
        )  # .replace is to remove spaces

        # create the file
        with self.cell_filename.open("w") as file:

            # first write the VARVOL line using predicted volume
            volume = composition.volume_estimate()
            file.write("#VARVOL={}".format(volume) + "\n")

            # write the SPECIES line
            line = "#SPECIES="
            for element in composition:
                line += element.symbol + "%NUM=" + str(int(composition[element])) + ", "
            line = line[:-2]  # remove the final ', '
            # write the line
            file.write(line + "\n")

            # write the MINSEP line. For now I just assume 1 Angstrom
            file.write("#MINSEP=1.0" + "\n")

    def create_structure(self) -> Structure:

        # TODO: Maybe make an AIRSS calculator / S3 workflow
        output = subprocess.run(
            "buildcell < {} | cabal cell cif > AIRSS_output.cif".format(
                self.cell_filename
            ),
            shell=True,
            capture_output=True,
            text=True,  # convert output from bytes to string
        )

        # check to see if it was successful
        if output.returncode == 1:
            # AIRSS failed to make the structure
            return False

        # convert the cif file to pymatgen Structure
        structure = Structure.from_file("AIRSS_output.cif")

        # and delete the cif file for cleanup
        os.remove("AIRSS_output.cif")

        return structure
