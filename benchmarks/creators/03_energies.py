# -*- coding: utf-8 -*-

import pandas
import plotly.graph_objects as go
from plotly.offline import plot

from simmate.utilities import get_directory
from simmate.workflows.utilities import get_workflow

NSAMPLES_PER_COMPOSITION = 500

CREATORS_TO_TEST = [
    "Simmate",
    "XtalOpt",
    "ASE",
    "PyXtal",
    "GASP",
    "AIRSS",
    "USPEX",
    "CALYPSO",
]

parent_dir = get_directory("creator_benchmarks")
# workflow_static = get_workflow("static-energy.vasp.quality04")
workflow_relax = get_workflow("relaxation.vasp.staged")


subplots = []
for creator_name in CREATORS_TO_TEST:

    data = workflow_relax.all_results.filter(
        energy_per_atom__isnull=False,
        source__creator=creator_name,
    ).values_list("energy_per_atom", "formula_reduced")

    # y should be all energy values for ALL compositions put together in to
    # a 1D array
    ys = [entry[0] for entry in data]
    # x should be labels that are the same length as the xs list
    xs = [entry[1] for entry in data]

    series = go.Box(
        name=creator_name,
        x=xs,
        y=ys,
        boxpoints=False,  # look at strip plots if you want the scatter points
    )
    subplots.append(series)

    # also write csv for safekeeping
    df = pandas.DataFrame(
        data=data,
        columns=[
            "energy_per_atom",
            "formula_reduced",
        ],
    )
    # df.to_csv(parent_dir / creator_name / "energies_initial.csv")
    df.to_csv(parent_dir / creator_name / "energies_final.csv")


layout = go.Layout(
    width=800,
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    boxmode="group",
    xaxis=dict(
        title_text="Composition",
        showgrid=False,
        ticks="outside",
        tickwidth=2,
        showline=True,
        color="black",
        linecolor="black",
        linewidth=2,
        mirror=True,
    ),
    yaxis=dict(
        title_text="Energy (eV/atom)",
        ticks="outside",
        tickwidth=2,
        showline=True,
        linewidth=2,
        color="black",
        linecolor="black",
        mirror=True,
    ),
    legend=dict(
        x=0.05,
        y=0.95,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    ),
)

fig = go.Figure(data=subplots, layout=layout)

plot(fig, config={"scrollZoom": True})
