# -*- coding: utf-8 -*-

# from simmate.apps.warrenapp.workflows.badelf.prebadelf_dft import (
#     StaticEnergy__Warren__PrebadelfHse,
# )
from simmate.apps.warrenapp.workflows.badelf.prebadelf_dft import (
    StaticEnergy__Warren__PrebadelfHse,
)
from simmate.apps.warrenapp.workflows.nested_dft.prepop_relaxation_static_pbesol_hse import (
    Relaxation__Warren__PbeWithWavecar,
)
from simmate.apps.warrenapp.workflows.nested_dft.relaxation_static_base import (
    RelaxationRelaxationStaticBase,
)
from simmate.apps.warrenapp.workflows.relaxation.hse import Relaxation__Warren__Hse


class Relaxation__Warren__HseWithWavecar(Relaxation__Warren__Hse):
    """
    This workflow is the same as the typical HSE relaxation but with the added
    tag in the INCAR for writing the WAVECAR. This is intended to be used with
    nested workflows to increase the speed of the static energy calculation
    """

    incar = Relaxation__Warren__Hse().incar.copy()
    incar.update(dict(LWAVE=True))


class Nested__Warren__RelaxationStaticHseHse(RelaxationRelaxationStaticBase):
    """
    Runs a PBEsol quality structure relaxation, an HSE quality relaxation, and
    an HSE static energy calculation. This method will also write the ELFCAR
    and CHGCAR files necessary for population analysis (i.e. oxidation state and
    electron count)
    """

    static_energy_workflow = StaticEnergy__Warren__PrebadelfHse
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
    low_quality_relaxation_workflow = Relaxation__Warren__PbeWithWavecar
    high_quality_relaxation_workflow = Relaxation__Warren__HseWithWavecar
