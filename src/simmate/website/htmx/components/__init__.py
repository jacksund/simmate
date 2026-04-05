# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from .base import HtmxComponent
from .mixins import MoleculeInput, StructureInput, UserInput
from .workflow_results import (
    BandStructureCalcTable,
    DensityofStatesCalcTable,
    DiffusionAnalysisTable,
    DynamicsIonicStepTable,
    DynamicsTable,
    IonicStepTable,
    MigrationHopTable,
    MigrationImageTable,
    PopulationAnalysisTable,
    RelaxationTable,
    StaticEnergyTable,
)
