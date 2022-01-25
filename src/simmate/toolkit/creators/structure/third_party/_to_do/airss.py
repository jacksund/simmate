# -*- coding: utf-8 -*-

from simmate.toolkit import Structure

# TODO: Maybe make an AIRSS calculator

#!!! NOT TESTED
class AIRSSStructure:

    # see source: https://www.mtg.msm.cam.ac.uk/Codes/AIRSS
    # see tutorials: https://airss-docs.github.io/

    def __init__(
        self,
        composition,  # must be a pymatgen Composition object
    ):

        # see if the user has AIRSS installed
        import subprocess

        #!!! what is the best way to see if AIRSS is installed? Check the path?
        output = subprocess.run(
            "airss.pl",  # command that calls AIRSS
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )
        if output.returncode == 1:
            #!!! I should raise an error in the future
            print("You must have AIRSS installed to use AIRSSStructure!!")
            return  # exit the function as the script will fail later on otherwise

        # to setup the AIRSS creator, we need to make a *.cell file that
        # for example, a SiO2 file will look like... (NOTE - the # symbols should be include in the file)
        # VARVOL=35
        # SPECIES=Si%NUM=1,O%NUM=2
        # MINSEP=1.0 Si-Si=3.00 Si-O=1.60 O-O=2.58

        # lets make this file and name it after the composition
        self.cell_filename = (
            composition.formula.replace(" ", "") + ".cell"
        )  # .replace is to remove spaces

        # create the file
        file = open(self.cell_filename, "w")

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

        # write the MINSEP line
        #!!! TO-DO for now I just assume 1 Angstrom
        file.write("#MINSEP=1.0" + "\n")

        # close the file
        file.close()

    def new_structure(self, spacegroup=None, lattice=None, species=None, coords=None):

        # if the user supplied a sites, it's going to be overwritten.
        if coords or species:
            #!!! this error will always show up in my current form of sample.py -- should I change that?
            #!!! the only time the error doesn't show up is when no validators fail on the object
            print(
                "Warning: AIRSS does not allow for specification of atomic sites and your "
                "specification here will be overwritten."
            )

        # if the user supplied a lattice, it's going to be overwritten.
        if lattice:
            print(
                "Warning: While AIRSS allows for specifying a fixed lattice, "
                "our wrapper does not currently support this. Contact our team if you"
                " would like this feature incorporated."
            )

        # if a spacegroup is not specified, grab a random one from our options
        # no check is done to see if the spacegroup specified is compatible with the vector_generator built
        if spacegroup:
            print(
                "Warning: AIRSS does not use symmetry to generate their structures "
                "and specifying this has no effect."
            )

        # now make the new structure using AIRSS scripts
        # NOTE: all of these options are set in the init except for the spacegroup
        #!!! should I add a timelimit?
        #!!! if I want to make this so I can make structures in parallel, I should reoranize the cif output naming
        import subprocess

        output = subprocess.run(
            "buildcell < {} | cabal cell cif > AIRSS_output.cif".format(
                self.cell_filename
            ),  # command that calls AIRSS #!!! subprocess prefers a list - should I change this?
            shell=True,  # use commands instead of local files
            capture_output=True,  # capture command output
            text=True,  # convert output from bytes to string
        )

        # check to see if it was successful
        if output.returncode == 1:
            # AIRSS failed to make the structure
            return False

        # convert the cif file to pymatgen Structure
        structure = Structure.from_file("AIRSS_output.cif")

        # and delete the cif file for cleanup
        import os

        os.remove("AIRSS_output.cif")

        return structure
