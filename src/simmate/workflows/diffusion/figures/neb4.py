# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import json
import numpy

from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalcd__energysteps_midpoint_json__isnull=False,
        vaspcalcb__energy_barrier__isnull=False,
        vaspcalcd__converged_start=True,
        vaspcalcd__converged_midpoint=True,
        vaspcalcd__converged_end=True,
        empiricalmeasures__ewald_energy__isnull=False,
    )
    .select_related("vaspcalcd", "vaspcalcb", "empiricalmeasures", "structure")
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
        "vaspcalcd__forces_start_json",
        "vaspcalcd__forces_midpoint_json",
        "vaspcalcd__forces_end_json",
        "vaspcalcd__stress_start_json",
        "vaspcalcd__stress_midpoint_json",
        "vaspcalcd__stress_end_json",
        "vaspcalcd__energysteps_start_json",
        "vaspcalcd__energysteps_midpoint_json",
        "vaspcalcd__energysteps_end_json",
        "vaspcalcd__timesteps_start_json",
        "vaspcalcd__timesteps_midpoint_json",
        "vaspcalcd__timesteps_end_json",
        "vaspcalcd__error_time_start",
        "vaspcalcd__error_time_midpoint",
        "vaspcalcd__error_time_end",
        "vaspcalcb__energy_barrier",
    ],
)

## FORCES
df["vaspcalcd__forces_start"] = df.vaspcalcd__forces_start_json.apply(json.loads)
df["vaspcalcd__forces_midpoint"] = df.vaspcalcd__forces_midpoint_json
df["vaspcalcd__forces_end"] = df.vaspcalcd__forces_end_json.apply(json.loads)

## STRESSES
df["vaspcalcd__stress_start"] = df.vaspcalcd__stress_start_json.apply(json.loads)
df["vaspcalcd__stress_midpoint"] = df.vaspcalcd__stress_midpoint_json.apply(json.loads)
df["vaspcalcd__stress_end"] = df.vaspcalcd__stress_end_json.apply(json.loads)

## TIMES
df["vaspcalcd__timesteps_start"] = df.vaspcalcd__timesteps_start_json.apply(json.loads)
df["vaspcalcd__timesteps_midpoint"] = df.vaspcalcd__timesteps_midpoint_json.apply(json.loads)
df["vaspcalcd__timesteps_end"] = df.vaspcalcd__timesteps_end_json.apply(json.loads)

## ENERGIES FOR ALL IONIC STEPS
df["vaspcalcd__energysteps_start"] = df.vaspcalcd__energysteps_start_json.apply(
    json.loads
)
df["vaspcalcd__energysteps_midpoint"] = df.vaspcalcd__energysteps_midpoint_json.apply(
    json.loads
)
df["vaspcalcd__energysteps_end"] = df.vaspcalcd__energysteps_end_json.apply(json.loads)


## ENERGIES
df["vaspcalcd__energysteps_barrier"] = [
    [max([m - s, m - e]) for s, m, e in zip(s_list, m_list, e_list)]
    for s_list, m_list, e_list in zip(
        df.vaspcalcd__energysteps_start,
        df.vaspcalcd__energysteps_midpoint,
        df.vaspcalcd__energysteps_end,
    )
]

# TOTAL TIMES AT EACH STEP
df["vaspcalcd__timesteps"] = [
    [sum([s,m,e]) for s, m, e in zip(s_list, m_list, e_list)]
    for s_list, m_list, e_list in zip(
        df.vaspcalcd__timesteps_start,
        df.vaspcalcd__timesteps_midpoint,
        df.vaspcalcd__timesteps_end,
    )
]

# --------------------------------------------------------------------------------------

# EXPERIMENTAL COLUMNS

# df["nsites_supercell_complex"] = df["nsites_101010"] / (df["nsites_777"] ** 2)

# df["forces_norm_start"] = df.vaspcalcd__forces_start.apply(numpy.linalg.norm)
# df["forces_norm_midpoint"] = df.vaspcalcd__forces_midpoint.apply(numpy.linalg.norm)
# df["forces_norm_end"] = df.vaspcalcd__forces_end.apply(numpy.linalg.norm)

# df["forces_norm_diff_initial"] = [
#     max([m - s, m - e])
#     for s, m, e in zip(
#         df.forces_norm_start,
#         df.forces_norm_midpoint,
#         df.forces_norm_end,
#     )
# ]

# df["forces_norm_complex"] = df["forces_norm_diff_initial"] * df["forces_norm_start"]

# --------------------------------------------------------------------------------------

df["total_time"] = df.vaspcalcd__timesteps.apply(sum)
df["nionic_steps"] = df.vaspcalcd__energysteps_start.apply(len)
df.plot(x="nionic_steps", y="total_time", c="nsites_777", kind="scatter", cmap="plasma", logy=True)

# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(50, 50))  # golden ratio = 1.618

gs = fig.add_gridspec(
    # grid dimensions and column/row relative sizes
    nrows=10,
    ncols=10,
    # width_ratios=(1, 1, 1),
    # height_ratios=(1, 1, 1),
    #
    # size of the overall grid (all axes together)
    left=0.1,
    right=0.9,
    bottom=0.1,
    top=0.9,
    #
    # spacing between subplots (axes)
    wspace=0.05,
    hspace=0.05,
)

for index in range(100):
    
    # try to grab the barrier for each. Some won't have one, in which case we
    # grab that last value
    approx_barriers = [
        pathway_barriers[index]
        if len(pathway_barriers) > index else pathway_barriers[-1]
        for pathway_barriers in df.vaspcalcd__energysteps_barrier
        ]

    # Add axes for the main plot
    ax = fig.add_subplot(
        gs[index // 10, index % 10],
        xlabel=f"IDPP-relaxed Barrier (eV) [NSW={index+1}]",
        ylabel=r"Midpoint-only NEB Barrier (eV)",
    )
    
    # add the data as a scatter
    hb = ax.scatter(
        x=approx_barriers,  # X
        y=df["vaspcalcb__energy_barrier"],  # Y
        c="Blue",  # COLOR
        alpha=0.6,  # Transparency
    )
    
    assert len(approx_barriers) == 80
    assert len(df["vaspcalcb__energy_barrier"]) == 80
    
    # add a y=x line through the ploy
    line = ax.plot(
        [-1, 1, 3],  # X
        [-1, 1, 3],  # Y
        c="Black",  # COLOR
    )

# plt.legend()
plt.show()

# --------------------------------------------------------------------------------------
