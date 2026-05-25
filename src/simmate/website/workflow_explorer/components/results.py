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
    StagedRelaxStatic,
    StaticEnergy,
)
from simmate.website.data_explorer.components import TableComponent


class StaticEnergyComponent(TableComponent):
    table = StaticEnergy
    display_name = "Static Energy"
    description_short = (
        "Results for Static Energy calculations, which determine the total "
        "energy of a fixed structure. These single-point calculations are "
        "fundamental for comparing the relative stability of different "
        "configurations."
    )
    template_names = {
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }


class RelaxationComponent(TableComponent):
    table = Relaxation
    display_name = "Relaxation"
    description_short = (
        "Results for geometry optimization (Relaxation) calculations. These "
        "simulations iteratively adjust atomic positions and lattice parameters "
        "to find the structure's lowest energy state."
    )
    template_names = {
        "entries": "workflow_explorer/relaxation/table.html",
        "entry": "workflow_explorer/relaxation/view.html",
    }


class StagedRelaxStaticComponent(TableComponent):
    table = StagedRelaxStatic
    display_name = "Staged Relax & Static"
    description_short = (
        "Results for a staged workflow that first relaxes the structure and "
        "then calculates the static energy. This is a common pattern for "
        "obtaining highly accurate energies."
    )
    template_names = {
        # Using the same templates as static energy or relaxation since it's a mix
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }


class PopulationAnalysisComponent(TableComponent):
    table = PopulationAnalysis
    display_name = "Population Analysis"
    description_short = (
        "Results for electronic population analysis, such as Bader charge analysis. "
        "These calculations partition the electron density among atoms to "
        "determine oxidation states and bonding characteristics."
    )


class DensityofStatesCalcComponent(TableComponent):
    table = DensityofStatesCalc
    display_name = "Density of States"
    description_short = (
        "Results for electronic density of states (DOS) calculations. These "
        "plots provide information on the number of electronic states per "
        "unit energy, essential for understanding metallic vs. insulating behavior."
    )
    template_names = {
        "entries": "workflow_explorer/density_of_states/table.html",
        "entry": "workflow_explorer/density_of_states/view.html",
    }


class BandStructureCalcComponent(TableComponent):
    table = BandStructureCalc
    display_name = "Band Structure"
    description_short = (
        "Results for electronic band structure calculations. These plots show "
        "the relationship between electron energy and momentum (k-points), "
        "providing a detailed map of the material's electronic properties."
    )
    template_names = {
        "entries": "workflow_explorer/band_structure/table.html",
        "entry": "workflow_explorer/band_structure/view.html",
    }


class DiffusionAnalysisComponent(TableComponent):
    table = DiffusionAnalysis
    display_name = "Diffusion Analysis"
    description_short = (
        "Results for kinetic diffusion analysis, including NEB (Nudged Elastic "
        "Band) calculations. These simulations map out the minimum energy "
        "path for ions migrating through a crystal lattice."
    )


class DynamicsComponent(TableComponent):
    table = Dynamics
    display_name = "Dynamics"
    description_short = (
        "Results for Molecular Dynamics (MD) simulations. These calculations "
        "evolve the system over time according to Newton's laws of motion, "
        "tracking temperature, pressure, and structural fluctuations."
    )


class IonicStepComponent(TableComponent):
    table = IonicStep


class MigrationHopComponent(TableComponent):
    table = MigrationHop


class MigrationImageComponent(TableComponent):
    table = MigrationImage


class DynamicsIonicStepComponent(TableComponent):
    table = DynamicsIonicStep
