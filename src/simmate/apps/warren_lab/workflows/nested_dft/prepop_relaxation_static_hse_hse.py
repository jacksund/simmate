# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.badelf.prebadelf_dft import (
    StaticEnergy__Vasp__WarrenLabPrebadelfHse,
)
from simmate.apps.warren_lab.workflows.nested_dft.prepop_relaxation_static_pbesol_hse import (
    Relaxation__Vasp__WarrenLabPbeWithWavecar,
)
from simmate.apps.warren_lab.workflows.nested_dft.relaxation_static_base import (
    RelaxationRelaxationStaticBase,
)
from simmate.apps.warren_lab.workflows.relaxation.hse import (
    Relaxation__Vasp__WarrenLabHse,
)


class Relaxation__Vasp__WarrenLabHseWithWavecar(Relaxation__Vasp__WarrenLabHse):
    """
    This workflow is the same as the typical HSE relaxation but with the added
    tag in the INCAR for writing the WAVECAR. This is intended to be used with
    nested workflows to increase the speed of the static energy calculation
    """

    _incar_updates = dict(LWAVE=True)


class Nested__Vasp__WarrenLabRelaxationStaticHseHse(RelaxationRelaxationStaticBase):
    """
    Runs a PBEsol quality structure relaxation, an HSE quality relaxation, and
    an HSE static energy calculation. This method will also write the ELFCAR
    and CHGCAR files necessary for population analysis (i.e. oxidation state and
    electron count)
    """

    static_energy_workflow = StaticEnergy__Vasp__WarrenLabPrebadelfHse
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
    low_quality_relaxation_workflow = Relaxation__Vasp__WarrenLabPbeWithWavecar
    high_quality_relaxation_workflow = Relaxation__Vasp__WarrenLabHseWithWavecar
