# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.apps.materials_project.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.apps.vasp.workflows.electronic_structure import ElectronicStructureWorkflow


class ElectronicStructure__Vasp__MatprojFull(ElectronicStructureWorkflow):
    """
    runs DOS and BS at Materials Project settings
    """

    static_energy_workflow = StaticEnergy__Vasp__Matproj
    band_structure_workflow = ElectronicStructure__Vasp__MatprojBandStructure
    density_of_states_workflow = ElectronicStructure__Vasp__MatprojDensityOfStates
