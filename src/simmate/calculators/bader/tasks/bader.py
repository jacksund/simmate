# -*- coding: utf-8 -*-

import os
import yaml
from pandas import DataFrame

from pymatgen.io.vasp.outputs import Chgcar
from pymatgen.io.vasp import Potcar

from simmate.toolkit import Structure
from simmate.workflow_engine import S3Task
from simmate.calculators.bader.outputs import ACF
from simmate.calculators.bader.tasks import CombineCHGCARs


class BaderAnalysis(S3Task):

    command = "bader CHGCAR -ref CHGCAR_sum -b weight > bader.out"
    """
    The command to call the executable, which is typically bader. Note we
    use the `-b weight` by default, which means we apply the weight method for
    partitioning from of 
    [Yu and Trinkle](http://theory.cm.utexas.edu/henkelman/code/bader/download/yu11_064111.pdf).
    
    This command is modified to use the `-ref` file as the reference for determining
    zero-flux surfaces when partitioning the CHGCAR. 
    
    There are cases where also use structures that contain "empty atoms" in them.
    This is to help with partitioning of electrides, which possess electron 
    density that is not associated with any atomic orbital. For these cases,
    you will see files like "CHGCAR_empty" used in the command.
    """

    required_files = ["CHGCAR", "AECCAR0", "AECCAR2", "POTCAR"]
    """
    In order for bader analysis to run properly, all of these files must be
    present in the provided directory.
    """
    # !!! Maybe move required_files attribute to the S3Task...? This could also
    # be useful for other tasks -- such as DOS and BS calculations. I could
    # then have an extra method that checks these before calling execute.

    def setup(self, structure: Structure, directory: str):
        """
        Bader analysis requires that a static-energy calculation be ran beforehand
        - typically using VASP. This setup therefore just involves ensuring that
        the proper files are present.
        """

        # Make sure that there are the proper output files from a VASP calc
        filenames = [os.path.join(directory, file) for file in self.required_files]
        if not all(os.path.exists(filename) for filename in filenames):
            raise Exception(
                "A static energy calculation is required before running Bader "
                "analysis. The following files must exist in the directory where "
                f"this task is ran: {self.required_files}"
            )

        # Make the CHGCAR_sum file using Bader's helper script
        CombineCHGCARs().run(directory=directory)

    def workup(self, directory: str):
        """
        A basic workup process that reads Bader analysis results from the ACF.dat
        file and calculates the corresponding oxidation states with the existing
        POTCAR files.
        """

        # load the ACF.dat file
        acf_filename = os.path.join(directory, "ACF.dat")
        dataframe, extra_data = ACF(filename=acf_filename)

        # load the electron counts used by VASP from the POTCAR files
        # OPTIMIZE: this can be much faster if I have a reference file
        potcar_filename = os.path.join(directory, "POTCAR")
        potcars = Potcar.from_file(potcar_filename)
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})

        # grab the structure from the CHGCAR
        # OPTIMIZE: I should just grab from the POSCAR or CONTCAR for speed.
        # The reason I don't at the moment is because there may be empty atoms.
        chgcar_filename = os.path.join(directory, "CHGCAR")
        chgcar = Chgcar.from_file(chgcar_filename)
        structure = chgcar.structure

        # Calculate the oxidation state of each site where it is simply the
        # change in number of electrons associated with it from vasp potcar vs
        # the bader charge I also add the element strings for filtering functionality
        elements = []
        oxi_state_data = []
        for site, site_charge in zip(structure, dataframe.charge.values):
            element_str = site.specie.name
            elements.append(element_str)
            oxi_state = nelectron_data[element_str] - site_charge
            oxi_state_data.append(oxi_state)

        # add the new column to the dataframe
        dataframe = dataframe.assign(
            oxidation_state=oxi_state_data,
            element=elements,
        )
        # !!! There are multiple ways to do this, but I don't know which is best
        # dataframe["oxidation_state"] = pandas.Series(
        #     oxi_state_data, index=dataframe.index)

        # write output files/plots for the user to quickly reference
        self._write_output_summary(directory, dataframe, extra_data)

        # return all of our results
        return dataframe, extra_data

    def _write_output_summary(
        self, directory: str, dataframe: DataFrame, extra_data: dict
    ):
        """
        This prints a "simmate_summary.yaml" file with key output information.

        This method should not be called directly as it used within workup().
        """

        # write output of the dataframe
        summary_csv_filename = os.path.join(directory, "simmate_summary_bader.csv")
        dataframe.to_csv(summary_csv_filename)

        summary = {
            "notes": "view simmate_summary_bader.csv for more information",
            **extra_data,
        }

        summary_filename = os.path.join(directory, "simmate_summary.yaml")
        with open(summary_filename, "w") as file:
            content = yaml.dump(summary)
            file.write(content)
