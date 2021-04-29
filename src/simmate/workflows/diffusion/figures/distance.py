# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------


from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalca__energy_barrier__isnull=False,
        vaspcalca__energy_barrier__gte=0,
        # empiricalmeasures__ionic_radii_overlap_anions__gt=-900,
    )
    .select_related("vaspcalca", "empiricalmeasures")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "length",
        "empiricalmeasures__ewald_energy",
        "empiricalmeasures__ionic_radii_overlap_anions",
        "empiricalmeasures__ionic_radii_overlap_cations",
        "vaspcalca__energy_barrier",
    ],
)

# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5*1.618, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"Pathway Length ($\AA$)",
    ylabel=r"$\Delta$ Ewald Energy (eV)",
    ylim=(-0.05, 1)
)

# add the data as a scatter
hb = ax.scatter(
    x=df["length"],  # X
    y=df["empiricalmeasures__ewald_energy"],  # Y
    c=df["vaspcalca__energy_barrier"], # COLOR
    cmap="RdYlGn_r",  # color scheme for colorbar
    vmax=7.5,  # upper limit of colorbar
)

# add the colorbar (for positioning we give it its own axes)
# where arg is [left, bottom, width, height]
cax = fig.add_axes([0.15, 0.825, 0.35, 0.03])
cb = fig.colorbar(
    hb,  # links color to hexbin
    cax=cax,  # links location to this axes
    orientation="horizontal",
    label=r"Energy Barrier (eV)",
)

plt.show()

# --------------------------------------------------------------------------------------

