# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------

### Fingerprint Comparison

import os
import numpy as np
import itertools
from pymatgen.core.structure import Structure

from matminer.featurizers.site import CrystalNNFingerprint as cnnf

sitefingerprint_method = cnnf.from_preset("ops", distance_cutoffs=None, x_diff_weight=3)

from pymatdisc.validators.fingerprint import (
    PartialsSiteStatsFingerprint,
)  #!!! this should move to matminer

featurizer = PartialsSiteStatsFingerprint(
    sitefingerprint_method, stats=["mean", "std_dev", "minimum", "maximum"]
)

# this is the total number of comparisons to be made
n_combos = len([1 for combo in itertools.combinations(range(n), 2)])
limit = 1000

# store all the distances here
distances_all = []

# iterate through the creator folders
for name in mapping:
    os.chdir(name)
    # pick the composition
    distances_creator = []
    for comp_str, comp_obj in track(zip(compositions_strs, compositions_objs)):
        if comp_str in ["Fe1"] and name == "ASE":  # Fails with...
            distances_creator.append([None] * limit)  #!!!
            continue
        os.chdir(comp_str)
        # fitting of the featurizer to the composition
        featurizer.elements_ = np.array(
            [element.symbol for element in comp_obj.elements]
        )
        # load the cifs
        structures = [
            Structure.from_file("{}.cif".format(i), primitive=True) for i in range(n)
        ]
        # calculate the fingerprint (in parallel)
        fingerprints = featurizer.featurize_many(structures, pbar=False)
        # calculate the distances for all combinations of structures
        distances_comp = [
            np.linalg.norm(combo[0] - combo[1])
            for combo in itertools.combinations(fingerprints, 2)
        ]
        if limit:
            distances_comp = np.random.choice(distances_comp, limit, replace=False)
        # add to ouput
        distances_creator.append(distances_comp)
        # move back to main directory
        os.chdir("..")
    os.chdir("..")
    distances_all.append(distances_creator)

    df = pandas.DataFrame(numpy.transpose(distances_creator), columns=compositions_strs)
    df.to_csv("{}_distances.csv".format(name))

# -----------------------------------------------------------------------------

### Plotting DistanceTest

import pandas

dfs = []
for name in mapping:
    df = pandas.read_csv("{}_distances.csv".format(name), index_col=0)
    dfs.append(df)

import plotly.graph_objects as go
from plotly.offline import plot

composition_strs = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    "Si4O8",
    "Al4O6",
    "Si4N4O2",
    "Sr4Si4N8",
    "Mg4Si4O12",
    "Mg8Si8O24",
]

data = []

for name, df in zip(mapping, dfs):
    # y should be all time values for ALL compositions put together in to a 1D array
    ys = df.values.flatten(order="F")
    # x should be labels that are the same length as the xs list
    xs = []
    for c in composition_strs:
        xs += [c] * limit  #!!!

    series = go.Box(
        name=name,
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
        title_text="Distance Between Fingerprints",
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

fig = go.Figure(data=data, layout=layout)

plot(fig, config={"scrollZoom": True})

# -----------------------------------------------------------------------------
