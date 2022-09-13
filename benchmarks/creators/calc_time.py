# -*- coding: utf-8 -*-

from rich.progress import track
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
]

parent_dir = get_directory("creator_benchmarks")
workflow_00 = get_workflow("relaxation.vasp.quality00")
workflow_relax = get_workflow("relaxation.vasp.staged")

subplots = []
for creator_name in CREATORS_TO_TEST:
    
    csv_file = parent_dir / creator_name / "total_calc_times.csv"
    if csv_file.exists():
        df = pandas.read_csv(csv_file)
        xs = list(df.formula_reduced.values)
        ys = list(df.total_time.values)

    else:
        data = workflow_relax.all_results.filter(
            energy_per_atom__isnull=False,
            source__creator=creator_name,
        ).values_list("id", "directory", "updated_at", "formula_reduced")
    
        xs = []
        ys = []
    
        for entry in track(data):
            id, directory, finished_at, formula = entry
    
            xs.append(formula)
            started_at = workflow_00.all_results.values("created_at").get(
                directory__startswith=directory,
            )["created_at"]
    
            total_time = (finished_at - started_at).total_seconds() / 60
    
            ys.append(total_time)
        
        # also write csv for safekeeping
        df = pandas.DataFrame(
            {"total_time": ys, "formula_reduced": xs}
        )
        # df.to_csv(parent_dir / creator_name / "energies_initial.csv")
        df.to_csv(csv_file)
    
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
        title_text="Calculation time (min)",
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
