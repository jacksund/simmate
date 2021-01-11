# -*- coding: utf-8 -*-

import os

from prefect.utilities.tasks import defaults_from_attrs

from simmate.workflows.core.tasks.stagedshelltask import StagedShellTask
from simmate.utilities import get_directory

from pymatgen.io.vasp.sets import DictSet
from pymatgen.io.vasp.outputs import Vasprun
from simmate.calculators.vasp.potcar_config import POTCAR_CONFIG

# ----------------------------------------------------------------------------

# !!! The warning that is raised here is because there is no YAML! It can be ignored
# TODO I need to rewrite DictSet so this warning goes away


class PreBaderInputSet(DictSet):

    CONFIG = {
        "INCAR": {
            "EDIFF": 1.0e-07,
            "EDIFFG": -1e-04,
            "ENCUT": 520,
            # 'ISIF': 3, #!!! do I want this..?
            "ISMEAR": 0,  # Guassian smearing #!!! read docs!
            "LCHARG": True,  # write CHGCAR
            "LAECHG": True,  # write AECCAR0, AECCAR1, and AECCAR2
            "LWAVE": False,
            "NSW": 0,  # single energy calc
            "PREC": "Accurate",
            "SIGMA": 0.05,
            # set FFT grid and fine FFT grid (note: start with fine!)
            # !!! YOU SHOULD EXPERIMENT WITH THESE UNTIL THEY CONVERGE THE BADER CHARGES
            # !!! SHOULD I MESS WITH NGX instead of NGXF???
            # 'NGX': 100,
            # 'NGY': 100,
            # 'NGZ': 100,
            # If prec = 'Single', then fine grid will automatically match
            # the NGX,Y,Z above and you don't need to set these.
            # 'NGXF': 100,
            # 'NGYF': 100,
            # 'NGZF': 100,
        },
        "KPOINTS": {"reciprocal_density": 25},
        **POTCAR_CONFIG,
    }

    def __init__(self, structure, **kwargs):
        """
        :param structure: Structure
        :param kwargs: Same as those supported by DictSet.
        """
        super().__init__(structure, PreBaderInputSet.CONFIG, **kwargs)
        self.kwargs = kwargs


# ----------------------------------------------------------------------------


class VASPPreBaderTask(StagedShellTask):
    command = "./bader CHGCAR -ref CHGCAR_sum -b weight > bader.out"
    requires_structure = True

    @defaults_from_attrs("dir", "structure")
    def setup(self, dir, structure):

        # TODO should I sanitize the structure first? primitive and LLL reduce?

        # write the input files
        inputset = PreBaderInputSet(structure)
        inputset.write_input(dir=dir)

    @defaults_from_attrs("dir")
    def postprocess(self, dir):
        """
        This is the most basic VASP workup where I simply load the final structure,
        final energy, and confirm convergence. I will likely make this a common
        function for this vasp module down the road.
        """

        # load the xml file and only parse the bare minimum
        xmlReader = Vasprun(
            filename=os.path.join(dir, "vasprun.xml"),
            parse_dos=False,
            parse_eigen=False,
            parse_projected_eigen=False,
            parse_potcar_file=False,
            exception_on_bad_xml=True,
        )

        # grab the final structure
        final_structure = xmlReader.structures[-1]

        # grab the energy per atom
        final_energy = xmlReader.final_energy / final_structure.num_sites

        # confirm that the calculation converged
        assert xmlReader.converged

        # return the desired info
        return final_structure, final_energy
