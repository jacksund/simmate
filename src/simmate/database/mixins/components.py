# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .band_structure import BandStructureCalc
from .density_of_states import DensityofStatesCalc
from .nudged_elastic_band import DiffusionAnalysis
from .dynamics import Dynamics
from .population_analysis import PopulationAnalysis
from .symmetry import Spacegroup


class BandStructureCalcTable(DynamicTableForm):
    table = BandStructureCalc
    html_display_name = "Band Structures"


class DensityofStatesCalcTable(DynamicTableForm):
    table = DensityofStatesCalc
    html_display_name = "Density of States"


class DiffusionAnalysisTable(DynamicTableForm):
    table = DiffusionAnalysis
    html_display_name = "Diffusion Analysis"


class DynamicsTable(DynamicTableForm):
    table = Dynamics
    html_display_name = "Dynamics"


class PopulationAnalysisTable(DynamicTableForm):
    table = PopulationAnalysis
    html_display_name = "Population Analysis"


class SpacegroupTable(DynamicTableForm):
    table = Spacegroup
    html_display_name = "Symmetry Spacegroups"
    html_description_short = (
        "Mathematical descriptions of the symmetry present in crystalline "
        "materials. Spacegroups categorize structures into 230 unique types "
        "based on their translational and point symmetry operations."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }
