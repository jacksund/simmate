# -*- coding: utf-8 -*-
from simmate.apps.warren_lab.workflows.static_energy.hse import (
    StaticEnergy__Vasp__WarrenLabHse,
)
from simmate.apps.warren_lab.workflows.static_energy.pbesol import (
    StaticEnergy__Vasp__WarrenLabPbesol,
)

# The key thing for bader analysis is that we need a very fine FFT mesh. Other
# than that, it's the same as a static energy calculation.
PREBADELF_INCAR_SETTINGS = dict(
    # Note that these set the FFT grid while the pre-Bader task sets the
    # fine FFT grid (e.g. useds NGX instead of NGXF)
    NGX__density_a=22,
    NGY__density_b=22,
    NGZ__density_c=22,
    LELF=True,  # Writes the ELFCAR
    NPAR=1,  # Must be set if LELF is set
    PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
    LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
)


class StaticEnergy__Vasp__WarrenLabPrebadelfPbesol(StaticEnergy__Vasp__WarrenLabPbesol):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    _incar_updates = PREBADELF_INCAR_SETTINGS


class StaticEnergy__Vasp__WarrenLabPrebadelfHse(StaticEnergy__Vasp__WarrenLabHse):
    """
    Runs a static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    _incar_updates = PREBADELF_INCAR_SETTINGS
