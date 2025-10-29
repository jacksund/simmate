# -*- coding: utf-8 -*-
from pathlib import Path

from baderkit.core import Grid, Bader
from simmate.workflows.base_flow_types import Workflow

from simmate.database import connect

from simmate.apps.baderkit.models.baderkit import BaderkitChargeAnalysis

class BaderkitChargeAnalysis__Baderkit__Bader(Workflow):
    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    use_database = True
    database_table = BaderkitChargeAnalysis
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    # parent_workflows = [
    #     "population-analysis.vasp-baderkit.bader-warren-lab",
    #     ]

    """
    Runs a Bader charge analysis on VASP outputs using the BaderKit package.
    """
    
    @classmethod
    def run_config(
        cls,
        previous_directory: Path,
        source: dict = None,
        directory: Path = None,
        run_id = None,
        baderkit_kwargs: dict = {},
        **kwargs,
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
            **baderkit_kwargs,
            )
        # get the table for this workflow and update entry
        datatable = cls.database_table.objects.get(run_id=run_id)
        datatable.update_from_baderkit(bader, directory)




