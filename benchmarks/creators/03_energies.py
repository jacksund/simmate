# -*- coding: utf-8 -*-

import pandas
import plotly.graph_objects as go
from plotly.offline import plot

from simmate.utilities import get_directory
from simmate.workflows.utilities import get_workflow

NSAMPLES_PER_COMPOSITION = 500

CREATORS_TO_TEST = [
    "Simmate",
    "Simmate (strict)",
    "XtalOpt",
    "ASE",
    "PyXtal",
    "GASP",
    "AIRSS",
    "USPEX",
    "CALYPSO",
]

parent_dir = get_directory("creator_benchmarks")


subplots = []
for creator_name in CREATORS_TO_TEST:

    workflow = get_workflow("static-energy.vasp.quality04")
    csv_file = parent_dir / creator_name / "energies_initial.csv"

    # workflow = get_workflow("relaxation.vasp.staged")
    # csv_file = parent_dir / creator_name / "energies_final.csv"

    if csv_file.exists():
        df = pandas.read_csv(csv_file)

    else:
        data = workflow.all_results.filter(
            energy_per_atom__isnull=False,
            source__creator=creator_name,
        ).values_list("energy_per_atom", "formula_reduced")

        # also write csv for safekeeping
        df = pandas.DataFrame(
            data=data,
            columns=[
                "energy_per_atom",
                "formula_reduced",
            ],
        )
        df.to_csv(csv_file)

    xs = list(df.formula_reduced.values)
    ys = list(df.energy_per_atom.values)

    series = go.Box(
        name=creator_name,
        x=xs,
        y=ys,
        boxpoints=False,  # look at strip plots if you want the scatter points
    )
    subplots.append(series)


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
        # x=0.05,
        # y=0.95,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    ),
)

fig = go.Figure(data=subplots, layout=layout)
fig.update_xaxes(
    categoryorder="array",
    categoryarray=[
        "Fe",
        "Si",
        "C",
        "TiO2",
        "SiO2",
        "Al2O3",
        "Si2N2O",
        "SrSiN2",
        "MgSiO3",
    ],
)

fig.write_image("energies.svg")
plot(fig, config={"scrollZoom": True})
