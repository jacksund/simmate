# -*- coding: utf-8 -*-
from .hse import (
    StaticEnergy__Vasp__WarrenLabHse,
)
from .pbesol import (
    StaticEnergy__Vasp__WarrenLabPbesol,
)
from .scan import StaticEnergy__Vasp__WarrenLabScan


class StaticEnergy__Vasp__WarrenLabPrebadelfPbesol(StaticEnergy__Vasp__WarrenLabPbesol):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    _incar_updates = dict(
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. uses NGX instead of NGXF)
        NGX__density_a=22,
        NGY__density_b=22,
        NGZ__density_c=22,
        NGXF__density_a=22,
        NGYF__density_b=22,
        NGZF__density_c=22,
        LELF=True,  # Writes the ELFCAR
        NPAR=1,  # Must be set if LELF is set
    )


class StaticEnergy__Vasp__WarrenLabPrebadelfHse(StaticEnergy__Vasp__WarrenLabHse):
    """
    Runs a static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    _incar_updates = dict(
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. uses NGX instead of NGXF)
        NGX__density_a=22,
        NGY__density_b=22,
        NGZ__density_c=22,
        NGXF__density_a=22,
        NGYF__density_b=22,
        NGZF__density_c=22,
        LELF=True,  # Writes the ELFCAR
        NPAR=1,  # Must be set if LELF is set
    )
    
class StaticEnergy__Vasp__WarrenLabPrebadelfScan(StaticEnergy__Vasp__WarrenLabScan):
    """
    Runs a static energy calculation with a high-density FFT grid under r2SCAN
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    _incar_updates = dict(
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. uses NGX instead of NGXF)
        NGX__density_a=22,
        NGY__density_b=22,
        NGZ__density_c=22,
        NGXF__density_a=22,
        NGYF__density_b=22,
        NGZF__density_c=22,
        LELF=True,  # Writes the ELFCAR
        NPAR=1,  # Must be set if LELF is set
    )