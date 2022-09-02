# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)


class VaspDensityOfStates(StaticEnergy__Vasp__Matproj):
    """
    A base class for density of states (DOS) calculations. This is not meant
    to be used directly but instead should be inherited from.

    This is also a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.
    """

    required_files = StaticEnergy__Vasp__Matproj.required_files + ["CHGCAR"]
