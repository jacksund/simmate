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
df["vaspcalcd__timesteps_midpoint"] = df.vaspcalcd__timesteps_midpoint_json.apply(
    json.loads
)
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
df["vaspcalcd__energysteps_barrier_errors"] = [
    [e - true_barrier for e in e_list]
    for e_list, true_barrier in zip(
        df.vaspcalcd__energysteps_barrier, df.vaspcalcb__energy_barrier
    )
]

# TOTAL TIMES AT EACH STEP
df["vaspcalcd__timesteps"] = [
    [sum([s, m, e]) for s, m, e in zip(s_list, m_list, e_list)]
    for s_list, m_list, e_list in zip(
        df.vaspcalcd__timesteps_start,
        df.vaspcalcd__timesteps_midpoint,
        df.vaspcalcd__timesteps_end,
    )
]

# CONVERGENCE DATA
df["vaspcalcd__energysteps_start_convergence"] = [
    [abs(e_list[i + 1] - e_list[i]) for i in range(len(e_list) - 1)]
    for e_list in df.vaspcalcd__energysteps_start
]
df["vaspcalcd__energysteps_midpoint_convergence"] = [
    [abs(e_list[i + 1] - e_list[i]) for i in range(len(e_list) - 1)]
    for e_list in df.vaspcalcd__energysteps_midpoint
]
df["vaspcalcd__energysteps_end_convergence"] = [
    [abs(e_list[i + 1] - e_list[i]) for i in range(len(e_list) - 1)]
    for e_list in df.vaspcalcd__energysteps_end
]

# --------------------------------------------------------------------------------------

df["total_time"] = df.vaspcalcd__timesteps.apply(sum)
df["nionic_steps"] = df.vaspcalcd__energysteps_start.apply(len)
df.plot(
    x="nionic_steps",
    y="total_time",
    c="nsites_777",
    kind="scatter",
    cmap="plasma",
    logy=True,
)

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(10, 10))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel="Ionic Step (#)",
    ylabel="Barrier Error (eV)",
    # ylim=(-0.05, 1)
)

data = df["vaspcalcd__energysteps_barrier_errors"].to_list()

for pathway in data:

    # add the data as a scatter
    hb = ax.plot(
        [i + 1 for i in range(len(pathway))],  # X
        pathway,  # Y
        # c=df["vaspcalca__energy_barrier"], # COLOR
        # cmap="RdYlGn_r",  # color scheme for colorbar
        # vmax=7.5,  # upper limit of colorbar
    )

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(10, 10))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel="Ionic Step (#)",
    ylabel="Average Barrier Error (eV)",
    # ylim=(-0.05, 1)
)

data = df["vaspcalcd__energysteps_barrier_errors"].to_list()

data_grouped_by_nsw_average = []
data_grouped_by_nsw_stddev = []
for nsw in range(100):
    approx_barriers = [
        pathway_barriers[nsw] if len(pathway_barriers) > nsw else pathway_barriers[-1]
        for pathway_barriers in df.vaspcalcd__energysteps_barrier_errors
    ]
    data_grouped_by_nsw_average.append(
        sum([abs(b) for b in approx_barriers]) / len(approx_barriers)
    )
    data_grouped_by_nsw_stddev.append(numpy.std(approx_barriers))

# add the data
hb = ax.errorbar(
    [n + 1 for n in range(100)],
    data_grouped_by_nsw_average,
    # yerr=data_grouped_by_nsw_stddev,
)

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(30, 10))  # golden ratio = 1.618

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
        pathway_barriers[int(index * 3)]
        if len(pathway_barriers) > index * 3
        else pathway_barriers[-1]
        for pathway_barriers in df.vaspcalcd__energysteps_barrier
    ]

    # Add axes for the main plot
    ax = fig.add_subplot(
        gs[index // 5, index % 5],
        xlabel=f"IDPP-relaxed Barrier (eV) [NSW={index*3+1}]",
        ylabel=r"Midpoint-only NEB Barrier (eV)",
    )

    # add the data as a scatter
    hb = ax.scatter(
        x=approx_barriers,  # X
        y=df["vaspcalcb__energy_barrier"],  # Y
        c="Blue",  # COLOR
        alpha=0.6,  # Transparency
    )

    # assert len(approx_barriers) == 80
    # assert len(df["vaspcalcb__energy_barrier"]) == 80

    # add a y=x line through the ploy
    line = ax.plot(
        [-1, 1, 3],  # X
        [-1, 1, 3],  # Y
        c="Black",  # COLOR
    )

# plt.legend()
plt.show()

# --------------------------------------------------------------------------------------

#### RECORD STATS
errors_relax_median = []
times_relax_median = []
errors_relax_std = []
times_relax_std = []
####

convergence_list = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0005]

for convergence in convergence_list:
    energies = []
    times = []
    # nionic_steps = []  # !!! consider adding
    for energysteps, timesteps, convsteps in zip(
        df.vaspcalcd__energysteps_start,
        df.vaspcalcd__timesteps_start,
        df.vaspcalcd__energysteps_start_convergence,
    ):
        for i, c in enumerate(convsteps):
            if c <= convergence:
                break
        # assert c <= convergence
        if c >= convergence:
            print(c, convergence)  # !!! THIS WILL REPORT ANY UNCONVERGED CALCS
        # print([sum(timesteps[:i]), c, energysteps[i], len(energysteps), i])
        energies.append(energysteps[i + 1])
        times.append(sum(timesteps[: i + 1]))
    df[f"energy_start_{convergence}"] = energies
    df[f"times_start_{convergence}"] = times
for convergence in convergence_list:
    energies = []
    times = []
    for energysteps, timesteps, convsteps in zip(
        df.vaspcalcd__energysteps_midpoint,
        df.vaspcalcd__timesteps_midpoint,
        df.vaspcalcd__energysteps_midpoint_convergence,
    ):
        for i, c in enumerate(convsteps):
            if c <= convergence:
                break
        # assert c <= convergence
        # print([sum(timesteps[:i]), c, energysteps[i]])
        energies.append(energysteps[i + 1])
        times.append(sum(timesteps[: i + 1]))
    df[f"energy_midpoint_{convergence}"] = energies
    df[f"times_midpoint_{convergence}"] = times
for convergence in convergence_list:
    energies = []
    times = []
    for energysteps, timesteps, convsteps in zip(
        df.vaspcalcd__energysteps_end,
        df.vaspcalcd__timesteps_end,
        df.vaspcalcd__energysteps_end_convergence,
    ):
        for i, c in enumerate(convsteps):
            if c <= convergence:
                break
        # assert c <= convergence
        # print([sum(timesteps[:i]), c, energysteps[i]])
        energies.append(energysteps[i + 1])
        times.append(sum(timesteps[: i + 1]))
    df[f"energy_end_{convergence}"] = energies
    df[f"times_end_{convergence}"] = times

####

for convergence in convergence_list:
    barriers = []
    errors = []
    times = []
    for s, m, e, actual in zip(
        df[f"energy_start_{convergence}"],
        df[f"energy_midpoint_{convergence}"],
        df[f"energy_end_{convergence}"],
        df["vaspcalcb__energy_barrier"],
    ):
        barrier = max([m - s, m - e])
        barriers.append(barrier)
        errors.append(barrier - actual)
    for s, m, e in zip(
        df[f"times_start_{convergence}"],
        df[f"times_midpoint_{convergence}"],
        df[f"times_end_{convergence}"],
    ):
        times.append(sum([s, m, e]) / (60 ** 2))

    df[f"times_{convergence}"] = times
    df[f"barriers_{convergence}"] = barriers
    df[f"errors_{convergence}"] = errors

####

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(20, 20))  # golden ratio = 1.618

gs = fig.add_gridspec(
    # grid dimensions and column/row relative sizes
    nrows=3,
    ncols=3,
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
    hspace=0.0,
)

for index, convergence in enumerate(convergence_list):

    # Add axes for the main plot
    ax = fig.add_subplot(
        gs[index // 3, index % 3],
        xlabel=f"IDPP-relaxed Barrier (eV) [EDIFFG={convergence}]",
        ylabel=r"Midpoint-only NEB Barrier (eV)",
    )

    # add the data as a scatter
    hb = ax.scatter(
        x=df[f"barriers_{convergence}"],  # X
        y=df["vaspcalcb__energy_barrier"],  # Y
        c="Blue",  # COLOR
        alpha=0.6,  # Transparency
    )

    # assert len(approx_barriers) == 80
    # assert len(df["vaspcalcb__energy_barrier"]) == 80

    # add a y=x line through the ploy
    line = ax.plot(
        [-1, 1, 3],  # X
        [-1, 1, 3],  # Y
        c="Black",  # COLOR
    )

# plt.legend()
plt.show()

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(10, 10))  # golden ratio = 1.618

gs = fig.add_gridspec(
    # grid dimensions and column/row relative sizes
    nrows=2,
    ncols=1,
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
    hspace=0.0,
)

ax1 = fig.add_subplot(
    gs[0, 0],
    xlabel="EDIFFG",
    ylabel="Barrier Error (eV)",
    # ylim=(-0.05, 1)
)

# Add NSW=0 first
zero_step_errors = [
    pathway_barriers[0] for pathway_barriers in df.vaspcalcd__energysteps_barrier_errors
]
hb = ax1.boxplot(
    zero_step_errors,
    labels=["static"],
    positions=[0],
    showfliers=False,
    patch_artist=True,
    meanline=True,
    showmeans=True,
    meanprops=dict(color='black'),
)
hb["boxes"][0].set_facecolor("lightblue")
errors_relax_median.append(
    numpy.median(zero_step_errors)
)
errors_relax_std.append(
    numpy.std(zero_step_errors)
)


# Add all steps
for index, convergence in enumerate(convergence_list):
    hb = ax1.boxplot(
        df[f"errors_{convergence}"],
        labels=[convergence],
        positions=[index + 1],
        showfliers=False,
        patch_artist=True,
        meanline=True,
        showmeans=True,
        meanprops=dict(color='black'),
    )
    hb["boxes"][0].set_facecolor("lightblue")
    errors_relax_median.append(
        numpy.median(df[f"errors_{convergence}"].dropna().to_numpy())
    )
    errors_relax_std.append(
        numpy.std(df[f"errors_{convergence}"].dropna().to_numpy())
    )

ax2 = fig.add_subplot(
    gs[1, 0],
    xlabel="EDIFFG",
    ylabel="Calculation Time (hrs)",
    sharex=ax1,
)

# Add NSW=0 first
zero_step_times = [timesteps[0] / (60 ** 2) for timesteps in df.vaspcalcd__timesteps]
hb = ax2.boxplot(
    zero_step_times,
    labels=["static"],
    positions=[0],
    showfliers=False,
    patch_artist=True,
    meanline=True,
    showmeans=True,
    meanprops=dict(color='black'),
)
hb["boxes"][0].set_facecolor("lightgreen")
times_relax_median.append(
    numpy.median(zero_step_times)
)
times_relax_std.append(
    numpy.std(zero_step_times)
)

for index, convergence in enumerate(convergence_list):

    # add the data as a boxplot
    hb = ax2.boxplot(
        df[f"times_{convergence}"],
        labels=[convergence],
        positions=[index + 1],
        showfliers=False,
        patch_artist=True,
        meanline=True,
        showmeans=True,
        meanprops=dict(color='black'),
    )

    hb["boxes"][0].set_facecolor("lightgreen")
    times_relax_median.append(
        numpy.median(df[f"times_{convergence}"].dropna().to_numpy())
    )
    times_relax_std.append(
        numpy.std(df[f"times_{convergence}"].dropna().to_numpy())
    )

ax1.tick_params(axis="x", labelbottom=False)

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(10, 10))  # golden ratio = 1.618

gs = fig.add_gridspec(
    # grid dimensions and column/row relative sizes
    nrows=2,
    ncols=1,
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
    hspace=0.0,
)

ax1 = fig.add_subplot(
    gs[0, 0],
    xlabel="Ionic Step (#)",
    ylabel="Barrier Error (eV)",
    # ylim=(-0.05, 1)
)

for nsw in range(10):
    approx_barriers = [
        pathway_barriers[nsw] if len(pathway_barriers) > nsw else pathway_barriers[-1]
        for pathway_barriers in df.vaspcalcd__energysteps_barrier_errors
    ]

    # add the data as a boxplot
    hb = ax1.boxplot(
        approx_barriers,
        labels=[nsw],
        positions=[nsw],
        showfliers=False,
        patch_artist=True,
        meanline=True,
        showmeans=True,
        meanprops=dict(color='black'),
    )
    hb["boxes"][0].set_facecolor("lightblue")


ax2 = fig.add_subplot(
    gs[1, 0],
    xlabel="Ionic Step (#)",
    ylabel="Calculation Time (hrs)",
    sharex=ax1,
)

for i in range(10):

    times = []
    for s, m, e in zip(
        df.vaspcalcd__timesteps_start,
        df.vaspcalcd__timesteps_midpoint,
        df.vaspcalcd__timesteps_end,
    ):
        x = sum(s[: i + 1]) if len(s) > nsw else sum(s)
        y = sum(m[: i + 1]) if len(m) > nsw else sum(m)
        z = sum(e[: i + 1]) if len(e) > nsw else sum(e)
        times.append(sum([x, y, z]) / (60 ** 2))

    # add the data as a boxplot
    hb = ax2.boxplot(
        times,
        labels=[i],
        positions=[i],
        showfliers=False,
        patch_artist=True,
        meanline=True,
        showmeans=True,
        meanprops=dict(color='black'),
    )
    hb["boxes"][0].set_facecolor("lightgreen")

ax1.tick_params(axis="x", labelbottom=False)

# --------------------------------------------------------------------------------------

import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(6, 6))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel="CPU Time (hrs)",
    ylabel="Error (eV)",
    # xlim=(0, 6),
    # ylim=(0, 0.5),
)

# add the data
hb = ax.errorbar(
    x=times_relax_median,
    y=errors_relax_median,
    # xerr=times_relax_std,
    yerr=errors_relax_std,
    fmt='--o',
    capsize=6,
)
