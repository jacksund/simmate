# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import json
import numpy

from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalcc__energy_barrier__isnull=False,
        vaspcalcb__energy_barrier__isnull=False,
        # vaspcalcb__energy_barrier__gte=-0.5,  # !!!
        empiricalmeasures__ewald_energy__isnull=False,
    )
    .select_related("vaspcalcc", "vaspcalcb", "empiricalmeasures", "structure")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "length",
        "atomic_fraction",
        "nsites_777",
        "nsites_101010",
        "structure__e_above_hull",
        "empiricalmeasures__ewald_energy",
        "vaspcalcc__forces_start_json",
        "vaspcalcc__forces_midpoint_json",
        "vaspcalcc__forces_end_json",
        "vaspcalcc__stress_start_json",
        "vaspcalcc__stress_midpoint_json",
        "vaspcalcc__stress_end_json",
        "vaspcalcc__energysteps_start_json",
        "vaspcalcc__energysteps_midpoint_json",
        "vaspcalcc__energysteps_end_json",
        "vaspcalcc__energy_start",
        "vaspcalcc__energy_midpoint",
        "vaspcalcc__energy_end",
        "vaspcalcc__energy_barrier",
        "vaspcalcb__energy_barrier",
    ],
)

## FORCES FOR FIRST IONIC STEP
df["vaspcalcc__forces_start"] = [
    json.loads(forces)[0] for forces in df.vaspcalcc__forces_start_json
]
df["vaspcalcc__forces_midpoint"] = [
    json.loads(forces)[0] for forces in df.vaspcalcc__forces_midpoint_json
]
df["vaspcalcc__forces_end"] = [
    json.loads(forces)[0] for forces in df.vaspcalcc__forces_end_json
]


## STRESS FOR FIRST IONIC STEP
df["vaspcalcc__stress_start"] = [
    json.loads(stress)[0] for stress in df.vaspcalcc__stress_start_json
]
df["vaspcalcc__stress_midpoint"] = [
    json.loads(stress)[0] for stress in df.vaspcalcc__stress_midpoint_json
]
df["vaspcalcc__stress_end"] = [
    json.loads(stress)[0] for stress in df.vaspcalcc__stress_end_json
]

## ENERGIES FOR ALL IONIC STEPS
df["vaspcalcc__energysteps_start"] = df.vaspcalcc__energysteps_start_json.apply(
    json.loads
)
df["vaspcalcc__energysteps_midpoint"] = df.vaspcalcc__energysteps_midpoint_json.apply(
    json.loads
)
df["vaspcalcc__energysteps_end"] = df.vaspcalcc__energysteps_end_json.apply(json.loads)


## ENERGIES FOR FIRST IONIC STEP
df["vaspcalcc__energy_start_initial"] = [e[0] for e in df.vaspcalcc__energysteps_start]
df["vaspcalcc__energy_midpoint_initial"] = [
    e[0] for e in df.vaspcalcc__energysteps_midpoint
]
df["vaspcalcc__energy_end_initial"] = [e[0] for e in df.vaspcalcc__energysteps_end]
df["vaspcalcc__energy_barrier_initial"] = [
    max([m - s, m - e])
    for s, m, e in zip(
        df.vaspcalcc__energy_start_initial,
        df.vaspcalcc__energy_midpoint_initial,
        df.vaspcalcc__energy_end_initial,
    )
]

# --------------------------------------------------------------------------------------


# EXPERIMENTAL COLUMNS

df["nsites_supercell_complex"] = df["nsites_101010"] / (df["nsites_777"] ** 2)


df["forces_norm_start"] = df.vaspcalcc__forces_start.apply(numpy.linalg.norm)
df["forces_norm_midpoint"] = df.vaspcalcc__forces_midpoint.apply(numpy.linalg.norm)
df["forces_norm_end"] = df.vaspcalcc__forces_end.apply(numpy.linalg.norm)

df["forces_norm_diff_initial"] = [
    max([m - s, m - e])
    for s, m, e in zip(
        df.forces_norm_start,
        df.forces_norm_midpoint,
        df.forces_norm_end,
    )
]

df["forces_norm_complex"] = df["forces_norm_diff_initial"] * df["forces_norm_start"]

# --------------------------------------------------------------------------------------

# The code below is for interactive plotting using Plotly
# import plotly.express as px

# fig = px.scatter(
#     data_frame=df,
#     x="vaspcalcc__energy_barrier_initial",
#     y="vaspcalcb__energy_barrier",
#     color="forces_norm_diff_initial",
#     # text="structure__id",
#     hover_data=[
#         "id",
#         "length",
#         # "structure__id",
#         # "structure__formula_full",
#         # "structure__spacegroup",
#         # "structure__formula_anonymous",
#         "nsites_supercell_ratio",
#         "structure__e_above_hull",
#         "empiricalmeasures__ewald_energy",
#         "forces_norm_diff_initial",
#         "vaspcalcc__energy_barrier",
#         "vaspcalcb__energy_barrier",
#         "forces_norm_start",
#         "forces_norm_midpoint",
#         "forces_norm_end"
#     ],
# )
# fig.show(renderer="browser", config={'scrollZoom': True})

# --------------------------------------------------------------------------------------

from sklearn import linear_model
from sklearn.model_selection import train_test_split

reg = linear_model.LinearRegression()
# reg = linear_model.Lasso(alpha=0.1)

# split our dataframe into training and test sets
# df_training, df_test = train_test_split(df, test_size=0.2)

# Fields to use in fitting
fields_to_fit = [
    "length",
    "nsites_777",
    # "nsites_supercell_complex",
    "forces_norm_diff_initial",
    # "forces_norm_complex",
    "structure__e_above_hull",
    "empiricalmeasures__ewald_energy",
    "vaspcalcc__energy_barrier_initial",
]

X_train = df[fields_to_fit]
y_train = df["vaspcalcb__energy_barrier"]
reg.fit(X_train, y_train)
coef = reg.coef_
r_2 = reg.score(X_train, y_train)
print(coef)
print(r_2)


# Now use our test set to see how the model does
X_test = df[fields_to_fit]
y_test_expected = df["vaspcalcb__energy_barrier"]
y_test_predicted = reg.predict(X_test)


# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV) [empirically corrected]",
    ylabel=r"Midpoint-only NEB Barrier (eV)",
    # xlim=(-0.5, 2.5),
    # ylim=(-0.5, 2.5),
)

# add the data as a scatter
hb = ax.scatter(
    x=y_test_predicted,  # X
    y=y_test_expected,  # Y
    c="Red",  # COLOR
    alpha=0.6,  # Transparency
    # marker=",",
)

# add a y=x line through the ploy
line = ax.plot(
    [-1, 1, 3],  # X
    [-1, 1, 3],  # Y
    c="Black",  # COLOR
)

plt.show()


test = y_test_expected - y_test_predicted
test.plot.hist("vaspcalcb__energy_barrier", bins=30)

# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV)",
    ylabel=r"Midpoint-only NEB Barrier (eV)",
    # xlim=(-0.5, 2.5),
    # ylim=(-0.5, 2.5),
)

# add the data as a scatter
hb = ax.scatter(
    x=df["vaspcalcc__energy_barrier"],  # !!! vaspcalcc__energy_barrier_initial
    y=df["vaspcalcb__energy_barrier"],  # Y
    c="Green",  # COLOR
    alpha=0.6,  # Transparency
)

# hb = ax.scatter(
#     x=df["vaspcalca__energy_barrier"],  # X
#     y=y_test_predicted,  # Y
#     c="Blue",  # COLOR
#     # alpha=0.6,  # Transparency
# )

# add a y=x line through the ploy
line = ax.plot(
    [-1, 1, 3],  # X
    [-1, 1, 3],  # Y
    c="Black",  # COLOR
)

plt.show()

test = df["vaspcalcb__energy_barrier"] - df["vaspcalcc__energy_barrier_initial"]
test.plot.hist("vaspcalcb__energy_barrier", bins=30)

# --------------------------------------------------------------------------------------


