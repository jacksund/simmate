# -*- coding: utf-8 -*-

import inspect
import math
from functools import cache
from pathlib import Path

import numpy
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots

from simmate.toolkit import Structure
from simmate.toolkit.visualization.plotting import PlotlyFigure

from ..core import Workflow


class StagedWorkflow(Workflow):
    """
    An abstract class for running a series of calculations. This workflow
    is meant to help build staged relaxations for evolutionary searches, but can
    be used for any series of calculations that use the results of the previous
    calculation.

    When inheriting this mixin, the database table should be the same as the
    final subworkflow or a custom table combining
    """

    description_doc_short = "runs a series of dft calculations"

    subworkflow_names = []  # The names of the workflows

    files_to_copy = []  # Files that should be copied from one run to the next

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        source: dict = None,
        directory: Path = None,
        subworkflow_kwargs: dict = None,
        **kwargs,
    ):
        subworkflow_kwargs = subworkflow_kwargs or {}
        subworkflow_ids = []
        failed_subworkflow = None
        result = None

        for i, current_task in enumerate(cls.subworkflows):
            new_directory = directory / current_task.name_full
            try:
                if i == 0:
                    result = current_task.run(
                        structure=structure,
                        directory=new_directory,
                        **subworkflow_kwargs,
                    )
                else:
                    result = current_task.run(
                        structure=result,  # this is the result of the last run
                        directory=new_directory,
                        previous_directory=result.directory,
                        **subworkflow_kwargs,
                    )
                subworkflow_ids.append(result.id)
            except Exception as e:
                print(str(e))
                failed_subworkflow = cls.subworkflow_strings[i]
                break

        # save final result
        final_result = dict(
            structure=structure,
            subworkflow_names=cls.subworkflow_strings,
            subworkflow_ids=subworkflow_ids,
            copied_files=cls.files_to_copy,
            failed_subworkflow=failed_subworkflow,
        )

        # In case we have a result (even if a later subworkflow failed) we
        # append the result of the last successful run to the final result
        if result is not None:
            final_result |= result.to_api_dict()

            # remove results that will conflict with the base calculation.
            # For example, we don't want to return a directory value because this
            # will be different from the base workflow. We also don't want to send
            # columns from the structure mixin because these are calculated directly
            # from the structure
            mixin_names = result.get_mixin_names()
            mixins = result.get_mixins()
            for name, mixin in zip(mixin_names, mixins):
                if name == "Structure" or name == "Calculation":
                    for calc_data in mixin.get_column_names():
                        final_result.pop(calc_data, None)

        return final_result

    @classmethod
    @property
    @cache
    def subworkflow_strings(cls):
        # The input "subworkflow_names" can be either workflows or their string
        # names. This is a convenience property to standardize them to strings
        return [
            name.name_full if inspect.isclass(name) else name
            for name in cls.subworkflow_names
        ]

    @classmethod
    @property
    @cache
    def subworkflows(cls):
        # import locally to avoid circular import
        from simmate.workflows.utils import get_workflow

        return [
            name if inspect.isclass(name) else get_workflow(name)
            for name in cls.subworkflow_names
        ]

    @classmethod
    @property
    @cache
    def last_subworkflow(cls):
        # This is just convenient for code clarity
        return cls.subworkflows[-1]

    @classmethod
    @property
    @cache
    def subworkflow_tables(cls):
        return list(dict.fromkeys(subflow.database_table for subflow in cls.subworkflows))

    @classmethod
    def get_series(cls, value: str, **filter_kwargs):
        # We pull the directories of all staged calculations where the final
        # result has the given filter criteria
        directories = (
            cls.last_subworkflow.all_results.filter(**filter_kwargs)
            .values_list("directory", flat=True)
            .all()
        )
        # The above filter returns the subfolder for the final calculation. We
        # just want the parent folder for this so we get it here
        directories = list({str(Path(d).parent) for d in directories})

        # Note, this method is optimized to grab ALL data up front in as few
        # queries as possible.
        subworkflow_names = cls.subworkflow_strings

        all_data = {w: {} for w in subworkflow_names}
        for table in cls.subworkflow_tables:
            # for each type of table, we filter for the provided kwargs. We then
            # return a query with the requested value, directory, and workflow name
            query = table.objects.filter(
                workflow_name__in=subworkflow_names,
                **filter_kwargs,
            ).values_list(value, "directory", "workflow_name")

            # For each result in our query we get the parent directory. We then
            # add the result to our all_data dictionary with the parent directory
            # as the key and requested value as the value.
            for output, directory, workflow_name in query:
                folder_base = str(Path(directory).parent)
                all_data[workflow_name].update({folder_base: output})

        all_value_series = []
        # We iterate over each staged workflow directory matching our criteria
        for directory in directories:
            value_series = [
                all_data[subflow.name_full].get(directory, numpy.nan)
                for subflow in cls.subworkflows
            ]
            all_value_series.append(value_series)

        return all_value_series



class StagedSeriesConvergence(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        fitness_field: str,
        **filter_kwargs,
    ):
        all_energy_series = workflow.get_series(
            value=fitness_field,
            **filter_kwargs,
        )

        num_transitions = len(workflow.subworkflows) - 1
        figure = make_subplots(
            rows=math.ceil(num_transitions / 3),
            cols=3,
        )

        for i in range(num_transitions):
            xs = [series[i + 1] for series in all_energy_series]
            ys = [series[i] for series in all_energy_series]

            row = math.ceil((i + 1) / 3)
            col = (i % 3) + 1

            figure.add_trace(
                trace=plotly_go.Scatter(x=xs, y=ys, mode="markers"),
                row=row,
                col=col,
            )

            # add a line for y=x for added visualization
            valid_vals = [v for v in xs + ys if v is not None and v == v]
            if valid_vals:
                x_min, x_max = min(valid_vals), max(valid_vals)
                figure.add_trace(
                    trace=plotly_go.Scatter(
                        x=[x_min, x_max],
                        y=[x_min, x_max],
                        mode="lines",
                        line=dict(dash="dash", color="black"),
                        name="y=x",
                    ),
                    row=row,
                    col=col,
                )

            # Update axes properties
            figure.update_xaxes(
                title_text=workflow.subworkflows[i + 1].name_full,
                row=row,
                col=col,
            )
            figure.update_yaxes(
                title_text=workflow.subworkflows[i].name_full,
                row=row,
                col=col,
            )

        figure.update_layout(
            title=f"{fitness_field} comparison for each stage",
            showlegend=False,
        )
        return figure


class StagedSeriesHistogram(PlotlyFigure):
    method_type = "classmethod"

    def get_plot(
        workflow,  # Relaxation__Vasp__Staged
        fitness_field: str,
        **filter_kwargs,
    ):
        all_energy_series = workflow.get_series(
            value=fitness_field,
            **filter_kwargs,
        )

        figure = plotly_go.Figure()

        for i in range(len(workflow.subworkflows) - 1):
            diffs = []
            for series in all_energy_series:
                v1, v2 = series[i], series[i + 1]
                if v1 is not None and v2 is not None and v1 == v1 and v2 == v2:
                    diffs.append(v2 - v1)

            figure.add_trace(
                trace=plotly_go.Histogram(
                    x=diffs,
                    name=(
                        f"{workflow.subworkflows[i].name_full} "
                        f"--> {workflow.subworkflows[i+1].name_full}"
                    ),
                )
            )

        figure.update_layout(
            barmode="overlay",
            xaxis_title_text=f"{fitness_field}",
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
    _plot.register_to_class(StagedWorkflow)
