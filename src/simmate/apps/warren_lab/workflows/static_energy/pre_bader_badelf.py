# -*- coding: utf-8 -*-
from simmate.apps.vasp.inputs.potcar_mappings import PBE_GW_POTCAR_MAPPINGS

from .hse import StaticEnergy__Vasp__HseWarren, StaticEnergy__Vasp__SpinHseWarren
from .pbesol import StaticEnergy__Vasp__PbesolWarren, StaticEnergy__Vasp__SpinPbesolWarren
from .scan import StaticEnergy__Vasp__ScanWarren, StaticEnergy__Vasp__SpinScanWarren

class StaticEnergy__Vasp__PrebaderWarren(StaticEnergy__Vasp__PbesolWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for Bader analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.

    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    _incar_updates = dict(
        NGXF__density_a=22,
        NGYF__density_b=22,
        NGZF__density_c=22,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
    )

_BADELF_INCAR = dict(
    # Note that these set the FFT grid while the pre-Bader task sets the
    # fine FFT grid (e.g. uses NGX instead of NGXF)
    NGX__density_a=22,
    NGY__density_b=22,
    NGZ__density_c=22,
    NGXF__density_a=22,
    NGYF__density_b=22,
    NGZF__density_c=22,
    LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
    LELF=True,  # Writes the ELFCAR
    NPAR=1,  # Must be set if LELF is set
)

class StaticEnergy__Vasp__PrebadelfPbesolWarren(StaticEnergy__Vasp__PbesolWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR


class StaticEnergy__Vasp__PrebadelfHseWarren(StaticEnergy__Vasp__HseWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR


class StaticEnergy__Vasp__PrebadelfScanWarren(StaticEnergy__Vasp__ScanWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under r2SCAN
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR

class StaticEnergy__Vasp__PrebadelfSpinPbesolWarren(StaticEnergy__Vasp__SpinPbesolWarren):
    """
    Runs a spin-polarized static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR


class StaticEnergy__Vasp__PrebadelfSpinHseWarren(StaticEnergy__Vasp__SpinHseWarren):
    """
    Runs a spin-polarized static energy calculation with a high-density FFT grid under HSE
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR

class StaticEnergy__Vasp__PrebadelfSpinScanWarren(StaticEnergy__Vasp__SpinScanWarren):
    """
    Runs a spin-polarized static energy calculation with a high-density FFT grid under r2SCAN
    settings from the Warren Lab. Results can be used for BadELF analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    _incar_updates = _BADELF_INCAR
    
class StaticEnergy__Vasp__PreRadiiWarren(StaticEnergy__Vasp__PbesolWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.

    See `bader.workflows.materials_project`.
    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    _incar_updates = dict(
        NGX__density_a=11,  # set grid and fine grid to same, reasonably accurate value
        NGY__density_b=11,
        NGZ__density_c=11,
        NGXF__density_a=11,
        NGYF__density_b=11,
        NGZF__density_c=11,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        LELF=True,  # write ELFCAR
        NPAR=1,  # must be set for ELF calc
    )
