# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import json
import numpy
import itertools

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
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(forces)]
    for forces in df.vaspcalcc__forces_start_json
]
df["vaspcalcc__forces_midpoint"] = [
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(forces)]
    for forces in df.vaspcalcc__forces_midpoint_json
]
df["vaspcalcc__forces_end"] = [
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(forces)]
    for forces in df.vaspcalcc__forces_end_json
]


## STRESS FOR FIRST IONIC STEP
df["vaspcalcc__stress_start"] = [
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(stress)]
    for stress in df.vaspcalcc__stress_start_json
]
df["vaspcalcc__stress_midpoint"] = [
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(stress)]
    for stress in df.vaspcalcc__stress_midpoint_json
]
df["vaspcalcc__stress_end"] = [
    [numpy.linalg.norm(ionic_step) for ionic_step in json.loads(stress)]
    for stress in df.vaspcalcc__stress_end_json
]

## ENERGIES FOR ALL IONIC STEPS
df["vaspcalcc__energysteps_start"] = df.vaspcalcc__energysteps_start_json.apply(
    json.loads
)
df["vaspcalcc__energysteps_midpoint"] = df.vaspcalcc__energysteps_midpoint_json.apply(
    json.loads
)
df["vaspcalcc__energysteps_end"] = df.vaspcalcc__energysteps_end_json.apply(json.loads)
df["vaspcalcc__energysteps_barrier"] = [
    [max([m - s, m - e]) for s, m, e in zip(sa, ma, ea)]
    for sa, ma, ea in zip(
        df.vaspcalcc__energysteps_start,
        df.vaspcalcc__energysteps_midpoint,
        df.vaspcalcc__energysteps_end,
    )
]


## ENERGIES FOR FIRST IONIC STEP
df["vaspcalcc__energy_start_initial"] = [e[0] for e in df.vaspcalcc__energysteps_start]
df["vaspcalcc__energy_midpoint_initial"] = [
    e[0] for e in df.vaspcalcc__energysteps_midpoint
]
df["vaspcalcc__energy_end_initial"] = [e[0] for e in df.vaspcalcc__energysteps_end]
df["vaspcalcc__energy_barrier_initial"] = [
    max([m - s, m - e])
    for s, m, e in itertools.zip_longest(
        df.vaspcalcc__energy_start_initial,
        df.vaspcalcc__energy_midpoint_initial,
        df.vaspcalcc__energy_end_initial,
        fillvalue=numpy.NaN
    )
]

# --------------------------------------------------------------------------------------

# import matplotlib.pyplot as plt

# for index, pathway in df.iterrows():

#     # start with a square Figure
#     fig = plt.figure(figsize=(25, 5))  # golden ratio = 1.618

#     gs = fig.add_gridspec(
#         # grid dimensions and column/row relative sizes
#         nrows=1,
#         ncols=3,
#         # width_ratios=(1, 1, 1),
#         # height_ratios=(1, 1, 1),
#         #
#         # size of the overall grid (all axes together)
#         left=0.1,
#         right=0.9,
#         bottom=0.1,
#         top=0.9,
#         #
#         # spacing between subplots (axes)
#         wspace=0.05,
#         hspace=0.05,
#     )

#     # Add axes for the main plot
#     ax1 = fig.add_subplot(
#         gs[0, 0],  # left subplot
#         xlabel=r"Ionic Step (#)",
#         ylabel=r"Energy (eV)",
#     )

#     # add the data as a scatter
#     hb = ax1.plot(
#         pathway.vaspcalcc__energysteps_start,
#         c="Red",  # COLOR
#         alpha=0.6,  # Transparency
#         label="start",
#     )

#     # add the data as a scatter
#     hb = ax1.plot(
#         pathway.vaspcalcc__energysteps_midpoint,
#         c="Green",  # COLOR
#         alpha=0.6,  # Transparency
#         label="midpoint",
#     )

#     # add the data as a scatter
#     hb = ax1.plot(
#         pathway.vaspcalcc__energysteps_end,
#         c="Blue",  # COLOR
#         alpha=0.6,  # Transparency
#         label="end",
#     )

#     # # Add axes for the main plot
#     # ax2 = fig.add_subplot(
#     #     gs[0, 1],  # left subplot
#     #     xlabel=r"Ionic Step (#)",
#     #     ylabel=r"Forces (norm)",
#     # )

#     # # add the data as a scatter
#     # hb = ax2.plot(
#     #     pathway.vaspcalcc__forces_start,
#     #     c="Red",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="start",
#     # )

#     # # add the data as a scatter
#     # hb = ax2.plot(
#     #     pathway.vaspcalcc__forces_midpoint,
#     #     c="Green",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="midpoint",
#     # )

#     # # add the data as a scatter
#     # hb = ax2.plot(
#     #     pathway.vaspcalcc__forces_end,
#     #     c="Blue",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="end",
#     # )

#     # # Add axes for the main plot
#     # ax3 = fig.add_subplot(
#     #     gs[0, 2],  # left subplot
#     #     xlabel=r"Ionic Step (#)",
#     #     ylabel=r"Stress (norm)",
#     # )

#     # # add the data as a scatter
#     # hb = ax3.plot(
#     #     pathway.vaspcalcc__stress_start,
#     #     c="Red",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="start",
#     # )

#     # # add the data as a scatter
#     # hb = ax3.plot(
#     #     pathway.vaspcalcc__stress_midpoint,
#     #     c="Green",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="midpoint",
#     # )

#     # # add the data as a scatter
#     # hb = ax3.plot(
#     #     pathway.vaspcalcc__stress_end,
#     #     c="Blue",  # COLOR
#     #     alpha=0.6,  # Transparency
#     #     label="end",
#     # )

#     plt.legend()
#     plt.show()

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

for index, pathway in df.iterrows():
    # print([index//10, index%10])

    # Add axes for the main plot
    ax = fig.add_subplot(
        gs[index // 10, index % 10],  # left subplot
        xlabel=r"Ionic Step (#)",
        ylabel=r"Barrier (eV)",
    )

    # # add the data as a scatter
    # hb = ax.plot(
    #     pathway.vaspcalcc__stress_start,
    #     c="Red",  # COLOR
    #     alpha=0.6,  # Transparency
    #     label="start",
    # )

    # # add the data as a scatter
    # hb = ax.plot(
    #     pathway.vaspcalcc__stress_midpoint,
    #     c="Green",  # COLOR
    #     alpha=0.6,  # Transparency
    #     label="midpoint",
    # )

    # # add the data as a scatter
    # hb = ax.plot(
    #     pathway.vaspcalcc__stress_end,
    #     c="Blue",  # COLOR
    #     alpha=0.6,  # Transparency
    #     label="end",
    # )
    
    # add the data as a scatter
    hb = ax.plot(
        pathway.vaspcalcc__energysteps_barrier,
        c="Black",  # COLOR
        alpha=0.6,  # Transparency
        label="end",
    )

# plt.legend()
plt.show()

# --------------------------------------------------------------------------------------

# start with a square Figure
fig = plt.figure(figsize=(25, 10))  # golden ratio = 1.618

gs = fig.add_gridspec(
    # grid dimensions and column/row relative sizes
    nrows=2,
    ncols=5,
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

for index in range(10):
    
    # try to grab the barrier for each. Some won't have one, in which case we
    # grab that last value
    approx_barriers = [
        pathway_barriers[index]
        if len(pathway_barriers) > index else  None # pathway_barriers[-1]
        for pathway_barriers in df.vaspcalcc__energysteps_barrier
        ]


    # Add axes for the main plot
    ax = fig.add_subplot(
        gs[index // 5, index % 5],
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
    
    # add a y=x line through the ploy
    line = ax.plot(
        [-1, 1, 3],  # X
        [-1, 1, 3],  # Y
        c="Black",  # COLOR
    )

# plt.legend()
plt.show()
