# -*- coding: utf-8 -*-

import os

from prefect.utilities.tasks import defaults_from_attrs

from simmate.workflow_engine import S3Task

from simmate.calculators.bader.outputs import ACF
from pymatgen.io.vasp.outputs import Chgcar
from pymatgen.io.vasp import Potcar

# TODO -- I should replace the chgsum.pl script with a simple python function
# that just sums the two files. It might not be as fast but it removes one
# executable file from having to be in the user's path.


class CombineCHGCARsTask(S3Task):
    command = "./chgsum.pl AECCAR0 AECCAR2 > chgsum.out"


class BaderAnalysisTask(S3Task):
    command = "./bader CHGCAR -ref CHGCAR_sum -b weight > bader.out"

    @defaults_from_attrs("dir")
    def setup(self, dir=None):

        # Make sure that there are CHGCAR, AECCAR0, AECCAR2 files from a VASP calc
        files = ["CHGCAR", "AECCAR0", "AECCAR2"]
        filenames = [os.path.join(dir, file) for file in files]
        assert all(os.path.exists(filename) for filename in filenames)

        # Make the CHGCAR_sum file using Bader's helper script
        CombineCHGCARsTask().run(dir=dir)

    @defaults_from_attrs("dir")
    def postprocess(self, dir=None):

        # load the ACF.dat file
        acf_filename = os.path.join(dir, "ACF.dat")
        dataframe, extra_data = ACF(filename=acf_filename)

        # load the electron counts used by VASP from the POTCAR files
        # OPTIMIZE this can be much faster if I have a reference file
        potcar_filename = os.path.join(dir, "POTCAR")
        potcars = Potcar.from_file(potcar_filename)
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})

        # grab the structure from the CHGCAR
        # OPTIMIZE I should just grab from the POSCAR or CONTCAR for speed
        chgcar = Chgcar.from_file("CHGCAR")
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
        # !!! There are multiple ways to do this, but I don't know which is best
        # dataframe["oxidation_state"] = pandas.Series(
        #     oxi_state_data, index=dataframe.index)
        dataframe = dataframe.assign(
            oxidation_state=oxi_state_data,
            element=elements,
        )

        # return all of our results
        return dataframe, extra_data
