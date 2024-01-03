# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.quantum_espresso.inputs.potentials_sssp import (
    SSSP_PBE_EFFICIENCY_MAPPINGS,
    SSSP_PBE_PRECISION_MAPPINGS,
)
from simmate.apps.quantum_espresso.settings import DEFAULT_PSUEDO_DIR, SIMMATE_QE_DOCKER
from simmate.toolkit import Structure


def keyword_modifier_pseudo_dir(structure: Structure, confirm_auto: bool) -> Path:
    """
    If `pseudo_dir__auto=True` is set, the user is requesting the default directory
    for psuedopotentials
    """
    assert confirm_auto
    if not SIMMATE_QE_DOCKER:  # used in the majority of cases
        return DEFAULT_PSUEDO_DIR
    else:
        return "/potentials"


def keyword_modifier_nat(structure: Structure, confirm_auto: bool) -> int:
    """
    If `nat__auto=True` is set, the user wants nat (number of atoms) set automatically
    """
    assert confirm_auto
    return len(structure)


def keyword_modifier_ntyp(structure: Structure, confirm_auto: bool) -> int:
    """
    If `ntyp__auto=True` is set, the user wants ntyp (number of species) set automatically
    """
    assert confirm_auto
    return len(structure.composition)


def keyword_modifier_ecutwfc(structure: Structure, mode: str) -> float:
    """
    If `ecutwfc__auto=True` is set, the user wants ecutwfc (Kinetic energy cutoff (Ry)
    for wavefunctions) set automatically. To do this, we look at all elements
    and their mapped psuedos. The mappings indicate a suggested value and we use
    the maximum across all elements.
    """
    if mode == "efficiency":
        mappings = SSSP_PBE_EFFICIENCY_MAPPINGS
    elif mode == "precision":
        mappings = SSSP_PBE_PRECISION_MAPPINGS
    else:
        raise Exception(f"Unknown mode set for ecutwfc__auto: {mode}")

    return max(
        [mappings[element.symbol]["cutoff_wfc"] for element in structure.composition]
    )


def keyword_modifier_ecutrho(structure: Structure, mode: str) -> float:
    """
    If `ecutrho__auto=True` is set, the user wants ecutrho (Kinetic energy cutoff (Ry)
    for charge density and potential) set automatically. To do this, we look at
    all elements and their mapped psuedos. The mappings indicate a suggested
    value and we use the maximum across all elements.
    """
    if mode == "efficiency":
        mappings = SSSP_PBE_EFFICIENCY_MAPPINGS
    elif mode == "precision":
        mappings = SSSP_PBE_PRECISION_MAPPINGS
    else:
        raise Exception(f"Unknown mode set for ecutrho__auto: {mode}")

    return max(
        [mappings[element.symbol]["cutoff_rho"] for element in structure.composition]
    )
