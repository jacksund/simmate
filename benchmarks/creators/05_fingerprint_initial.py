# -*- coding: utf-8 -*-

import itertools

import numpy as np
import pandas
import plotly.graph_objects as go
from dask.distributed import Client
from matminer.featurizers.site import CrystalNNFingerprint as cnnf
from matminer.featurizers.structure.sites import (
    SiteStatsFingerprint as pssf,  # PartialsSiteStatsFingerprint
)
from plotly.offline import plot
from rich.progress import track

from simmate.toolkit import Composition, Structure
from simmate.utilities import get_directory

client = Client()

COMPOSITIONS_TO_TEST = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    "Si4O8",
    "Al4O6",
    "Si4N4O2",
    "Sr4Si4N8",
    "Mg4Si4O12",
]
compositions = [Composition(c) for c in COMPOSITIONS_TO_TEST]

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

sitefingerprint_method = cnnf.from_preset("ops", distance_cutoffs=None, x_diff_weight=3)
featurizer = pssf(
    sitefingerprint_method, stats=["mean", "std_dev", "minimum", "maximum"]
)

parent_dir = get_directory("creator_benchmarks")

limit = 10000
plot_series = []
for creator_name in CREATORS_TO_TEST:

    csv_file = parent_dir / creator_name / "initial_fingergprint_distances.csv"

    if csv_file.exists():
        df = pandas.read_csv(csv_file, index_col=0)
    else:
        distances_creator = []
        for composition in track(compositions):
            directory = parent_dir / creator_name / str(composition)
            if not directory.exists():
                distances_creator.append(np.array([None] * limit))
                continue
            structures = []
            for file in directory.iterdir():
                structure = Structure.from_file(file)
                structures.append(structure)

            # ------------

            # this is the total number of comparisons to be made
            n = len(structures)
            n_combos = len([1 for combo in itertools.combinations(range(n), 2)])

            # ------------

            # fitting of the featurizer to the composition
            featurizer.elements_ = np.array(
                [element.symbol for element in composition.elements]
            )

            # calculate the fingerprint (in parallel)
            futures = []
            for s in structures:
                future = client.submit(featurizer.featurize, s, pure=False)
                futures.append(future)
            fingerprints = [f.result() for f in futures]
            # calculate the distances for all combinations of structures
            distances_comp = [
                np.linalg.norm(np.array(combo[0]) - np.array(combo[1]))
                for combo in itertools.combinations(fingerprints, 2)
            ]
            if limit:
                distances_comp = np.random.choice(distances_comp, limit, replace=False)

            distances_creator.append(distances_comp)

        df = pandas.DataFrame(
            np.transpose(distances_creator),
            columns=COMPOSITIONS_TO_TEST,
        )
        df.to_csv(csv_file)

    # y should be all time values for ALL compositions put together in to a 1D array
    ys = df.values.flatten(order="F")
    # x should be labels that are the same length as the xs list
    xs = []
    for c in compositions:
        xs += [c.formula] * limit

    series = go.Box(
        name=creator_name,
        x=xs,
        y=ys,
        boxpoints=False,  # look at strip plots if you want the scatter points
    )
    plot_series.append(series)

# -----------------------------------------------------------------------------

### Plotting DistanceTest

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
        title_text="Fingerprint Distance",
        # type="log",
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

fig = go.Figure(data=plot_series, layout=layout)

plot(fig, config={"scrollZoom": True})

# -----------------------------------------------------------------------------
