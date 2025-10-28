# -*- coding: utf-8 -*-
from pathlib import Path

from baderkit.core import Grid, Bader
from baderkit.core.bader.methods import Method
from simmate.workflows.base_flow_types import Workflow

from simmate.database import connect

class PopulationAnalysis__Baderkit__Bader(Workflow):
    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    use_database = False
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    parent_workflows = [
        "population-analysis.vasp-baderkit.bader-warren-lab",
        ]

    """
    Runs a Bader charge analysis on VASP outputs using the BaderKit package.
    """
    
    @staticmethod
    def run_config(
        source: dict = None,
        directory: Path = None,
        method: str | Method = "weight",
            ):
        # create CHGCAR_sum grid
        grid1 = Grid.from_vasp(directory / "AECCAR0")
        grid2 = Grid.from_vasp(directory / "AECCAR2")
        reference_grid = grid1.linear_add(grid2)
        # load CHGCAR
        charge_grid = Grid.from_vasp(directory / "CHGCAR")
        # create Bader
        bader = Bader(
            charge_grid=charge_grid,
            reference_grid=reference_grid,
            method=method
            )
        # get oxidation states
        oxidation_states = bader.get_oxidation_from_potcar(directory / "POTCAR")
        # create results dict matching output from Henkelman Bader
        results = {
            "oxidation_states": oxidation_states,
            "charges": bader.atom_charges,
            "min_dists": bader.basin_min_surface_distances,
            "volumes": bader.atom_volumes,
            "element_list": [i.species_string for i in bader.structure],
            "vacuum_charge": bader.vacuum_charge,
            "vacuum_volume": bader.vacuum_volume,
            "nelectrons": bader.total_electron_number,
            }
        return results




