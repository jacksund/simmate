# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.badelf.core import Grid


def chgsum(directory: Path):
    aeccar0 = Grid.from_file(directory / "AECCAR0")
    aeccar2 = Grid.from_file(directory / "AECCAR2")

    data_total0 = aeccar0.total
    data_total2 = aeccar2.total

    data_total_sum = data_total0 + data_total2

    new_grid = Grid(
        total=data_total_sum,
        diff=None,
        structure=aeccar0.structure,
        data_type="charge density",
    )

    new_grid.write_file("CHGCAR_sum")
