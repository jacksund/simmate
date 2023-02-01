# -*- coding: utf-8 -*-

import pandas
import plotly.graph_objects as go
from plotly.offline import plot
from rich.progress import track

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

static_workflow = get_workflow("static-energy.vasp.quality04")
relax_workflow = get_workflow("relaxation.vasp.staged")
workflow_00 = get_workflow("relaxation.vasp.quality00")

csv_file = parent_dir / "energy_change_vs_calc_time.csv"
if csv_file.exists():
    df = pandas.read_csv(csv_file)

else:
    data = relax_workflow.all_results.filter(
        energy_per_atom__isnull=False,
        source__creator__in=CREATORS_TO_TEST,
    ).all()

    formulas = []
    total_cpu_times = []
    initial_energies = []
    final_energies = []
    energy_changes = []

    for entry in track(data):
        # grab total cpu time
        started_at = workflow_00.all_results.values("created_at").get(
            directory__startswith=entry.directory,
        )["created_at"]
        finished_at = entry.updated_at
        total_time = (finished_at - started_at).total_seconds() / 60

        # grab change in energy
        try:
            initial_energy = static_workflow.all_results.values("energy_per_atom").get(
                source__file=entry.source["file"]
            )["energy_per_atom"]
            energy_change = entry.energy_per_atom - initial_energy

        except:
            print(entry.id)
            continue

        formulas.append(entry.formula_reduced)
        total_cpu_times.append(total_time)
        initial_energies.append(initial_energy)
        final_energies.append(entry.energy_per_atom)
        energy_changes.append(energy_change)

    # also write csv for safekeeping
    df = pandas.DataFrame(
        {
            "total_time": total_cpu_times,
            "formula": formulas,
            "initial_energy": initial_energies,
            "final_energy": final_energies,
            "energy_change": energy_changes,
        }
    )
    df.to_csv(csv_file)

subplots = []
for formula in df.formula.unique():
    df_filtered = df[df.formula == formula]

    series = go.Scatter(
        name=formula,
        x=df_filtered.energy_change,
        y=df_filtered.total_time,
        mode="markers",
    )
    subplots.append(series)


layout = go.Layout(
    width=800,
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    boxmode="group",
    xaxis=dict(
        title_text="Energy change (eV/atom)",
        showgrid=False,
        # type="log",
        ticks="outside",
        tickwidth=2,
        showline=True,
        color="black",
        linecolor="black",
        linewidth=2,
        mirror=True,
    ),
    yaxis=dict(
        title_text="CPU time (min)",
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

fig.write_image("energies_change_vs_time.svg")
plot(fig, config={"scrollZoom": True})
