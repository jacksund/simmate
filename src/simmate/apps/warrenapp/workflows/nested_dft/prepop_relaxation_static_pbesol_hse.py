# -*- coding: utf-8 -*-
from simmate.apps.warrenapp.workflows.nested_dft.relaxation_static_base import RelaxationStaticBase
from simmate.apps.warrenapp.workflows.population_analysis.prebader_badelf_dft import (
    StaticEnergy__Warren__PrebadelfHse,
)
from simmate.apps.warrenapp.workflows.relaxation.pbesol import Relaxation__Warren__Pbesol


# We want to run a PBE relaxation followed by an HSE static energy calculation.
# Copying the WAVECAR will make this much faster, but this requires that a
# WAVECAR exists. However, we generally don't want all relaxation calculations
# to save the WAVECAR so we make a custom workflow here.
class Relaxation__Warren__PbeWithWavecar(Relaxation__Warren__Pbesol):
    """
    This workflow is the same as the typical PBEsol relaxation but with the added
    tag in the INCAR for writing the WAVECAR. This is intended to be used with
    nested workflows to increase the speed of the static energy calculation
    """

    incar = Relaxation__Warren__Pbesol().incar.copy()
    incar.update(dict(LWAVE=True))


class Nested__Warren__RelaxationStaticPbeHse(RelaxationStaticBase):
    """
    Runs a PBEsol quality structure relaxation, an HSE quality static energy
    calculation.
    """

    static_energy_workflow = StaticEnergy__Warren__PrebadelfHse
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
    relaxation_workflow = Relaxation__Warren__PbeWithWavecar
