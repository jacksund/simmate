# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.electronic_structure.matproj_band_structure_hse import (
    ElectronicStructure__Vasp__MatprojBandStructureHse,
)
from simmate.apps.materials_project.workflows.electronic_structure.matproj_density_of_states_hse import (
    ElectronicStructure__Vasp__MatprojDensityOfStatesHse,
)
from simmate.apps.materials_project.workflows.static_energy.matproj_hse import (
    StaticEnergy__Vasp__MatprojHse,
)
from simmate.apps.vasp.workflows.electronic_structure import ElectronicStructureWorkflow


class ElectronicStructure__Vasp__MatprojHseFull(ElectronicStructureWorkflow):
    """
    runs DOS and BS at Materials Project settings
    """

    description_doc_short = "runs DOS and BS at Materials Project settings"

    # table not implemented yet. This is a placeholder
    database_table = ElectronicStructure__Vasp__MatprojBandStructureHse.database_table

    static_energy_workflow = StaticEnergy__Vasp__MatprojHse
    band_structure_workflow = ElectronicStructure__Vasp__MatprojDensityOfStatesHse
    density_of_states_workflow = ElectronicStructure__Vasp__MatprojBandStructureHse
