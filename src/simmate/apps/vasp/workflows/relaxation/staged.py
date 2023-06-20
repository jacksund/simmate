# -*- coding: utf-8 -*-

import math
from functools import cache
from pathlib import Path

import numpy
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots

from simmate.engine import Workflow
from simmate.toolkit import Structure
from simmate.visualization.plotting import PlotlyFigure
from simmate.workflows.utilities import get_workflow


class Relaxation__Vasp__Staged(Workflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
    """

    exlcude_from_archives = [
        "CHG",
        "CHGCAR",
        "DOSCAR",
        "EIGENVAL",
        "IBZKPT",
        "OSZICAR",
        "OUTCAR",
        "PCDAT",
        "POTCAR",
        "REPORT",
        "WAVECAR",
        "XDATCAR",
    ]

    description_doc_short = "runs a series of relaxations (00-04 quality)"

    subworkflow_names = [
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
        "relaxation.vasp.quality03",
        "relaxation.vasp.quality04",
        "static-energy.vasp.quality04",
    ]

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
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
            "site_forces": result.site_forces,
            "lattice_stress": result.lattice_stress,
        }
        return final_result

    @classmethod
    @property
    @cache
    def subworkflows(cls):
        return [get_workflow(name) for name in cls.subworkflow_names]

    @classmethod
    def get_series(cls, value: str, **filter_kwargs):
        directories = (
            cls.all_results.filter(**filter_kwargs).values_list("directory", flat=True)
            # .order_by("?")[:1000]
            .all()
        )

        # Note, this method is optimized to grab ALL data up front in as few
        # queries as possible. We grab all data rather than many smaller queries.
        # Smaller queries are clear for code. The method would simplify to...
        #
        # for directory in directories:
        #     for subflow in cls.subworkflows:
        #         query = subflow.database_table.objects.filter(
        #             workflow_name=subflow.name_full,
        #             directory__startswith=directory,
        #             **filter_kwargs,
        #         ).values_list(value)
        #
        # Thererfore everything below is just minimizing the number of queries
        # and reformatting the data output of the complex query.

        tables = []
        for subflow in cls.subworkflows:
            if subflow.database_table not in tables:
                tables.append(subflow.database_table)

        all_data = {w: {} for w in cls.subworkflow_names}
        for table in tables:
            query = table.objects.filter(
                workflow_name__in=cls.subworkflow_names,
                **filter_kwargs,
            ).values_list(value, "directory", "workflow_name")

            # This filter crashes at large query sizes. It's actually more stable
            # and efficient to grab ALL data and filter out results in python.
            # from django.db.models import Q as dj_query
            # complex_filter = dj_query(
            #     *[("directory__startswith", d) for d in directories],
            #     _connector=dj_query.OR,
            # )
            # .filter(complex_filter)

            for output, directory, workflow_name in query:
                folder_base = str(Path(directory).parent)

                # this is the replacement for the commented-out complex filter
                # shown above
                # if folder_base not in directories:
                #     continue

                all_data[workflow_name].update({folder_base: output})

        all_value_series = []
        for directory in directories:
            value_series = []
            for subflow in cls.subworkflows:
                new_value = all_data[subflow.name_full].get(directory, numpy.nan)
                value_series.append(new_value)
            all_value_series.append(value_series)

        return all_value_series


class StagedSeriesConvergence(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        **filter_kwargs,
    ):
        all_energy_series = workflow.get_series(
            value="energy_per_atom",
            **filter_kwargs,
        )

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
        all_energy_series = workflow.get_series(
            value="energy_per_atom",
            **filter_kwargs,
        )

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


class StagedSeriesTimes(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        **filter_kwargs,
    ):
        all_time_series = workflow.get_series(
            value="total_time",
            **filter_kwargs,
        )

        figure = plotly_go.Figure()

        all_time_series = numpy.transpose(all_time_series)
        all_time_series = all_time_series / 60  # convert to minutes
        traces = []
        for i, times in enumerate(all_time_series):
            trace = plotly_go.Histogram(
                x=times,
                name=f"{workflow.subworkflows[i].name_full}",
            )
            traces.append(trace)

        # add them to the figure in reverse, so that the first relaxations are
        # in the front and not hidden
        traces.reverse()
        for trace in traces:
            figure.add_trace(trace=trace)

        figure.update_layout(
            barmode="overlay",
            xaxis_title_text="Calculation time (min)",
            yaxis_title_text="Structures (#)",
            bargap=0.05,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
            ),
        )
        figure.update_traces(opacity=0.75)
        return figure


# register all plotting methods to the database table
for _plot in [StagedSeriesConvergence, StagedSeriesHistogram, StagedSeriesTimes]:
    _plot.register_to_class(Relaxation__Vasp__Staged)
