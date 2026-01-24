# -*- coding: utf-8 -*-
from simmate.apps.vasp.inputs.potcar_mappings import PBE_GW_POTCAR_MAPPINGS

from .hse import StaticEnergy__Vasp__HseWarren
from .pbesol import StaticEnergy__Vasp__PbesolWarren
from .scan import StaticEnergy__Vasp__ScanWarren


class StaticEnergy__Vasp__PrebadelfPbesolWarren(StaticEnergy__Vasp__PbesolWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

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


class StaticEnergy__Vasp__PrebadelfHseWarren(StaticEnergy__Vasp__HseWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

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


class StaticEnergy__Vasp__PrebadelfScanWarren(StaticEnergy__Vasp__ScanWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under r2SCAN
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

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
