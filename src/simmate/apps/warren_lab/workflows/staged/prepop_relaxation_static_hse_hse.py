# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hse import (
    Relaxation__Vasp__HseWarren,
)
from simmate.workflows.base_flow_types import StagedWorkflow


class Relaxation__Vasp__HseWithWavecarWarren(Relaxation__Vasp__HseWarren):
    """
    This workflow is the same as the typical HSE relaxation but with the added
    tag in the INCAR for writing the WAVECAR. This is intended to be used with
    nested workflows to increase the speed of the static energy calculation
    """

    _incar_updates = dict(LWAVE=True)


class StaticEnergy__Vasp__RelaxationStaticHseHseWarren(StagedWorkflow):
    """
    Runs a PBEsol quality structure relaxation, an HSE quality relaxation, and
    an HSE static energy calculation. This method will also write the ELFCAR
    and CHGCAR files necessary for population analysis (i.e. oxidation state and
    electron count)
    """

    subworkflow_names = [
        "relaxation.vasp.warren-lab-pbesol-with-wavecar",
        "relaxation.vasp.warren-lab-hse-with-wavecar",
        "static-energy.vasp.warren-lab-prebadelf-hse",
    ]
    files_to_copy = ["WAVECAR"]
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
