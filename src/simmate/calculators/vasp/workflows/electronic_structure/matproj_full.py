# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.electronic_structure.base import (
    ElectronicStructureWorkflow,
)
from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)


class ElectronicStructure__Vasp__MatprojFull(ElectronicStructureWorkflow):
    """
    runs DOS and BS at Materials Project settings
    """

    description_doc_short = "runs DOS and BS at Materials Project settings"

    # table not implemented yet. This is a placeholder
    database_table = ElectronicStructure__Vasp__MatprojBandStructure.database_table

    static_energy_workflow = StaticEnergy__Vasp__Matproj
    band_structure_workflow = ElectronicStructure__Vasp__MatprojDensityOfStates
    density_of_states_workflow = ElectronicStructure__Vasp__MatprojBandStructure
