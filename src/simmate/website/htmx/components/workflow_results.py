# -*- coding: utf-8 -*-

from simmate.database.mixins import (
    BandStructureCalc,
    DensityofStatesCalc,
    DiffusionAnalysis,
    Dynamics,
    DynamicsIonicStep,
    IonicStep,
    MigrationHop,
    MigrationImage,
    PopulationAnalysis,
    Relaxation,
    StaticEnergy,
)
from simmate.website.htmx.components import DynamicTableForm


class StaticEnergyTable(DynamicTableForm):
    table = StaticEnergy
    display_name = "Static Energy"
    description_short = (
        "Results for Static Energy calculations, which determine the total "
        "energy of a fixed structure. These single-point calculations are "
        "fundamental for comparing the relative stability of different "
        "configurations."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }


class RelaxationTable(DynamicTableForm):
    table = Relaxation
    display_name = "Relaxation"
    description_short = (
        "Results for geometry optimization (Relaxation) calculations. These "
        "simulations iteratively adjust atomic positions and lattice parameters "
        "to find the structure's lowest energy state."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/relaxation/table.html",
        "entry": "workflow_explorer/relaxation/view.html",
    }


class PopulationAnalysisTable(DynamicTableForm):
    table = PopulationAnalysis
    display_name = "Population Analysis"
    description_short = (
        "Results for electronic population analysis, such as Bader charge analysis. "
        "These calculations partition the electron density among atoms to "
        "determine oxidation states and bonding characteristics."
    )


class DensityofStatesCalcTable(DynamicTableForm):
    table = DensityofStatesCalc
    display_name = "Density of States"
    description_short = (
        "Results for electronic density of states (DOS) calculations. These "
        "plots provide information on the number of electronic states per "
        "unit energy, essential for understanding metallic vs. insulating behavior."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/density_of_states/table.html",
        "entry": "workflow_explorer/density_of_states/view.html",
    }


class BandStructureCalcTable(DynamicTableForm):
    table = BandStructureCalc
    display_name = "Band Structure"
    description_short = (
        "Results for electronic band structure calculations. These plots show "
        "the relationship between electron energy and momentum (k-points), "
        "providing a detailed map of the material's electronic properties."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/band_structure/table.html",
        "entry": "workflow_explorer/band_structure/view.html",
    }


class DiffusionAnalysisTable(DynamicTableForm):
    table = DiffusionAnalysis
    display_name = "Diffusion Analysis"
    description_short = (
        "Results for kinetic diffusion analysis, including NEB (Nudged Elastic "
        "Band) calculations. These simulations map out the minimum energy "
        "path for ions migrating through a crystal lattice."
    )


class DynamicsTable(DynamicTableForm):
    table = Dynamics
    display_name = "Dynamics"
    description_short = (
        "Results for Molecular Dynamics (MD) simulations. These calculations "
        "evolve the system over time according to Newton's laws of motion, "
        "tracking temperature, pressure, and structural fluctuations."
    )


class IonicStepTable(DynamicTableForm):
    table = IonicStep


class MigrationHopTable(DynamicTableForm):
    table = MigrationHop


class MigrationImageTable(DynamicTableForm):
    table = MigrationImage


class DynamicsIonicStepTable(DynamicTableForm):
    table = DynamicsIonicStep
