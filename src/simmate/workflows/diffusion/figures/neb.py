# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------


from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalca__energy_barrier__isnull=False,
        vaspcalcb__energy_barrier__isnull=False,
        # empiricalmeasures__ionic_radii_overlap_anions__gt=-900,
    )
    .select_related("vaspcalca", "vaspcalcb")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "vaspcalca__energy_barrier",
        "vaspcalcb__energy_barrier",
    ],
)

# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV)",
    ylabel=r"Midpoint-only NEB Barrier (eV)",
    xlim=(-0.05, 2),
    ylim=(-0.05, 2),
)

# add a y=x line through the ploy
line = ax.plot(
    [-1, 1, 3],  # X
    [-1, 1, 3],  # Y
    c="Black", # COLOR
)

# add the data as a scatter
hb = ax.scatter(
    x=df["vaspcalca__energy_barrier"],  # X
    y=df["vaspcalcb__energy_barrier"],  # Y
    c="Green", # COLOR
)

plt.show()

# --------------------------------------------------------------------------------------

