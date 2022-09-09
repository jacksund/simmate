# -*- coding: utf-8 -*-

import math

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
from simmate.visualization.plotting import PlotlyFigure
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
                structure=result,  # this is the result of the last run
                command=command,
                directory=directory / current_task.name_full,
            )
            result = state.result()

        # when updating the original entry, we want to use the data from the
        # final result.
        final_result = {
            "structure": result.to_toolkit(),
            "energy": result.energy,
            "band_gap": result.band_gap,
            "is_gap_direct": result.is_gap_direct,
            "energy_fermi": result.energy_fermi,
            "conduction_band_minimum": result.conduction_band_minimum,
            "valence_band_maximum": result.valence_band_maximum,
        }
        return final_result

    @classmethod
    def get_energy_series(cls, **filter_kwargs):
        directories = (
            cls.all_results.filter(**filter_kwargs)
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

        return all_energy_series


class StagedSeriesConvergence(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        **filter_kwargs,
    ):
        all_energy_series = workflow.get_energy_series(**filter_kwargs)

        figure = make_subplots(
            rows=math.ceil((len(workflow.subworkflows) - 1) / 3),
            cols=3,
        )

        for i in range(len(workflow.subworkflows) - 1):

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
                title_text=f"{workflow.subworkflows[i + 1].name_full}",
                row=row,
                col=col,
            )
            figure.update_yaxes(
                title_text=workflow.subworkflows[i].name_full,
                row=row,
                col=col,
            )

        figure.update_layout(
            title="Energy per atom (eV) comparison for each stage",
            showlegend=False,
        )
        return figure


class StagedSeriesHistogram(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        **filter_kwargs,
    ):

        all_energy_series = workflow.get_energy_series(**filter_kwargs)

        figure = plotly_go.Figure()

        for i in range(len(workflow.subworkflows) - 1):

            diffs = []
            for energy_series in all_energy_series:
                if energy_series[i + 1] and energy_series[i]:
                    d = energy_series[i + 1] - energy_series[i]
                    diffs.append(d)

            scatter = plotly_go.Histogram(
                x=diffs,
                name=(
                    f"{workflow.subworkflows[i].name_full} "
                    f"--> {workflow.subworkflows[i+1].name_full}"
                ),
            )
            figure.add_trace(trace=scatter)

        figure.update_layout(
            barmode="overlay",
            xaxis_title_text="Energy per atom change (eV)",
            yaxis_title_text="Structures (#)",
            bargap=0.05,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
            ),
        )

        return figure


# register all plotting methods to the database table
for _plot in [StagedSeriesConvergence, StagedSeriesHistogram]:
    _plot.register_to_class(Relaxation__Vasp__Staged)
