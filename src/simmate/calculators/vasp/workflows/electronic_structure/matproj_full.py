# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.electronic_structure.base_full import (
    ElectronicStructureWorkflow,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)


class ElectronicStructure__Vasp__MatprojFull(ElectronicStructureWorkflow):
    """
    runs DOS and BS at Materials Project settings
    """

    static_energy_workflow = StaticEnergy__Vasp__Matproj
    band_structure_workflow = ElectronicStructure__Vasp__MatprojDensityOfStates
    density_of_states_workflow = ElectronicStructure__Vasp__MatprojBandStructure
