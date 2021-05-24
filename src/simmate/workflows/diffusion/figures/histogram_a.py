# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------


from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import VaspCalcA

queryset = VaspCalcA.objects.filter(
    energy_barrier__isnull=False,
).all()
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=["energy_barrier"],
)

# --------------------------------------------------------------------------------------


import matplotlib.pyplot as plt

# start with a square Figure
fig = plt.figure(figsize=(5*1.68, 5))  # golden ratio = 1.618

# Add axes for the main plot
ax = fig.add_subplot(
    xlabel=r"IDPP-relaxed Barrier (eV)",
    ylabel=r"Number of Pathways (#)",
    xlim=(-3, 15),
    # ylim=(-0.05, 2),
)

# add the data as a scatter
hb = ax.hist(
    x=df["energy_barrier"],  # X
    bins=150,
    color="black",
    edgecolor="white",
    linewidth=0.5,
)

plt.show()

# --------------------------------------------------------------------------------------
