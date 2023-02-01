# -*- coding: utf-8 -*-

import shutil
import subprocess

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.base import StructureCreator
from simmate.utilities import get_directory


class AirssStructure(StructureCreator):
    """
    Creates structures using the AIRSS software package.

    source: https://www.mtg.msm.cam.ac.uk/Codes/AIRSS
    tutorials: https://airss-docs.github.io/
    installation: https://airss-docs.github.io/getting-started/installation/

    Dev Notes:

    To install...
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

    def __init__(
        self,
        composition: Composition,
        command: str = "buildcell",
    ):
        # check that the command exists
        if not shutil.which(command):
            raise Exception(
                "You must have AIRSS installed to use AirssStructure."
                "See https://airss-docs.github.io/getting-started/installation/"
            )
        self.command = command

        self.temp_dir = get_directory()  # leave empty to allow parallel

        # to setup the AIRSS creator, we need to make a *.cell file that
        # for example, a SiO2 file will look like... (NOTE - the # symbols
        # should be included in the file):
        # VARVOL=35
        # SPECIES=Si%NUM=1,O%NUM=2
        # MINSEP=1.0 Si-Si=3.00 Si-O=1.60 O-O=2.58
        self.cell_filename = self.temp_dir / "input.cell"
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
        # TODO: Maybe make an AIRSS app / S3 workflow
        output = subprocess.run(
            f"buildcell < {self.cell_filename} | cabal cell cif > AIRSS_output.cif",
            shell=True,
            capture_output=True,
            cwd=self.temp_dir,
        )

        # check to see if it was successful
        if output.returncode == 1:
            # AIRSS failed to make the structure
            return False

        # convert the cif file to pymatgen Structure
        filename = self.temp_dir / "AIRSS_output.cif"
        structure = Structure.from_file(filename)

        # and delete the cif file for cleanup
        filename.unlink()

        return structure
