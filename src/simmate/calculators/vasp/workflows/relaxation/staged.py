# -*- coding: utf-8 -*-

import math
from pathlib import Path

import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots

from simmate.calculators.vasp.workflows.relaxation.quality00 import (
    Relaxation__Vasp__Quality00,
)
from simmate.calculators.vasp.workflows.relaxation.quality01 import (
    Relaxation__Vasp__Quality01,
)
from simmate.calculators.vasp.workflows.relaxation.quality02 import (
    Relaxation__Vasp__Quality02,
)
from simmate.calculators.vasp.workflows.relaxation.quality03 import (
    Relaxation__Vasp__Quality03,
)
from simmate.calculators.vasp.workflows.relaxation.quality04 import (
    Relaxation__Vasp__Quality04,
)
from simmate.calculators.vasp.workflows.static_energy.quality04 import (
    StaticEnergy__Vasp__Quality04,
)
from simmate.workflow_engine import Workflow

# from simmate.calculators.vasp.database.relaxation import StagedRelaxation


class Relaxation__Vasp__Staged(Workflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation.vasp.quality00
        - relaxation.vasp.quality01
        - relaxation.vasp.quality02
        - relaxation.vasp.quality03
        - relaxation.vasp.quality04
        - static-energy.vasp.quality04

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
    """

    description_doc_short = "runs a series of relaxations (00-04 quality)"
    # database_table = StagedRelaxation

    subworkflows = [
        Relaxation__Vasp__Quality00,
        Relaxation__Vasp__Quality01,
        Relaxation__Vasp__Quality02,
        Relaxation__Vasp__Quality03,
        Relaxation__Vasp__Quality04,
        StaticEnergy__Vasp__Quality04,
    ]

    @classmethod
    def run_config(
        cls,
        structure,
        command=None,
        source=None,
        directory=None,
        copy_previous_directory=False,
        **kwargs,
    ):

        # Our first relaxation is directly from our inputs.
        current_task = cls.subworkflows[0]
        state = current_task.run(
            structure=structure,
            command=command,
            directory=directory / current_task.name_full,
        )
        result = state.result()

        # The remaining tasks continue and use the past results as an input
        for i, current_task in enumerate(cls.subworkflows[1:]):
            preceding_task = cls.subworkflows[i]  # will be one before because of [:1]
            state = current_task.run(
                structure={
                    "database_table": preceding_task.database_table.__name__,
                    "directory": result["directory"],  # uses preceding result
                    "structure_field": "structure_final",
                },
                command=command,
                directory=directory / current_task.name_full,
            )
            result = state.result()

        # we return the final step but update the directory to the parent one
        result["directory"] = directory
        return result

    @classmethod
    def _get_final_energy_series(cls, df, directory: str):
        """
        A utility that grabs the final energies from each stage. Useful for
        grabbing convergence information.
        """
        for subflow in cls.subworkflows:
            pass

    @classmethod
    def get_series_convergence_plot(cls, **filter_kwargs):

        directories = (
            cls.database_table.objects.filter(
                workflow_name=cls.name_full,
                **filter_kwargs,
            )
            .values_list("directory", flat=True)
            .all()
        )

        all_energy_series = []
        for directory in directories:
            energy_series = []
            for subflow in cls.subworkflows:
                query = subflow.database_table.objects.filter(
                    workflow_name=subflow.name_full,
                    directory__startswith=directory,
                    energy_per_atom__isnull=False,
                ).only("energy_per_atom")
                if query.exists():
                    result = query.get()
                    energy_series.append(result.energy_per_atom)
                else:
                    energy_series.append(None)
            all_energy_series.append(energy_series)

        # -------

        figure = make_subplots(
            rows=math.ceil((len(cls.subworkflows) - 1) / 3),
            cols=3,
        )

        for i in range(len(cls.subworkflows) - 1):

            xs = []
            ys = []
            for energy_series in all_energy_series:

                xs.append(energy_series[i + 1])
                ys.append(energy_series[i])

            scatter = plotly_go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
            )
            row = math.ceil((i + 1) / 3)
            col = (i % 3) + 1
            figure.add_trace(
                trace=scatter,
                row=row,
                col=col,
            )

            # Update xaxis properties
            figure.update_xaxes(
                title_text=cls.subworkflows[i + 1].name_full,
                row=row,
                col=col,
            )
            figure.update_yaxes(
                title_text=cls.subworkflows[i].name_full,
                row=row,
                col=col,
            )

        return figure

    @classmethod
    def view_series_convergence_plot(cls, **kwargs):
        figure = cls.get_series_convergence_plot(**kwargs)
        figure.show(renderer="browser")

    @classmethod
    def write_series_convergence_plot(cls, directory: Path, **kwargs):
        figure = cls.get_series_convergence_plot(**kwargs)
        figure.write_html(
            directory / "convergence__staged_relaxations.html",
            include_plotlyjs="cdn",
        )
