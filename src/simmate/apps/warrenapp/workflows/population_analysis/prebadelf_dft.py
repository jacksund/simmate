# -*- coding: utf-8 -*-
from simmate.apps.warrenapp.workflows.static_energy.hse import StaticEnergy__Warren__Hse
from simmate.apps.warrenapp.workflows.static_energy.pbesol import StaticEnergy__Warren__Pbesol

# We want to define the settings that will be used when updating static energy
# workflows for prebadelf DFT calculations. We do that here so that we don't
# need to do it in every inheriting class.

prebadelf_incar_settings = dict(
    NGX__density_a=10,  # Note that these set the FFT grid while the pre-Bader task sets the
    NGY__density_b=10,  # fine FFT grid (e.g. useds NGX instead of NGXF)
    NGZ__density_c=10,
    LELF=True,  # Writes the ELFCAR
    NPAR=1,  # Must be set if LELF is set
    PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
    LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
)

class StaticEnergy__Warren__PrebadelfPbesol(StaticEnergy__Warren__Pbesol):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = StaticEnergy__Warren__Pbesol.incar.copy()
    incar.update(prebadelf_incar_settings)


class StaticEnergy__Warren__PrebadelfHse(StaticEnergy__Warren__Hse):
    """
    Runs a static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = StaticEnergy__Warren__Hse.incar.copy()
    incar.update(prebadelf_incar_settings)
