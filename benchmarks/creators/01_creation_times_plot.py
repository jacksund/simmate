# -*- coding: utf-8 -*-


import pandas
import plotly.graph_objects as go
from plotly.offline import plot

from simmate.utilities import get_directory

CREATORS_TO_TEST = [
    "Simmate",
    "Simmate (strict)",  # 0.75 packing factor for dist cutoffs
    "XtalOpt",
    "ASE",
    "PyXtal",
    "GASP",
    "AIRSS",
    "USPEX",
    "CALYPSO",
]


parent_dir = get_directory("creator_benchmarks")

data = []

for creator_name in CREATORS_TO_TEST:

    directory = parent_dir / creator_name

    df = pandas.read_csv(directory / "times.csv", index_col=0)

    # y should be all time values for ALL compositions put together in to a 1D array
    ys = df.values.flatten(order="F")
    # x should be labels that are the same length as the xs list
    xs = []

    for c in df.columns:
        xs += [c] * len(df.index)

    series = go.Box(
        name=creator_name,
        x=xs,
        y=ys,
        boxpoints=False,  # look at strip plots if you want the scatter points
    )
    data.append(series)


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
        title_text="Time to Generate Single Structure (s)",
        type="log",
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

fig = go.Figure(data=data, layout=layout)

plot(fig, config={"scrollZoom": True})

# -----------------------------------------------------------------------------
