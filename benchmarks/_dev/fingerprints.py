# -*- coding: utf-8 -*-

# This is some old code that I have not updated yet for Simmate

#############################################################################

from pymatgen import MPRester

mpr = MPRester("2Tg7uUvaTAPHJQXl")

# Get structures. I import a bunch of test cases, but I'll do the testing with perovskite.
diamond = mpr.get_structure_by_material_id("mp-66")
gaas = mpr.get_structure_by_material_id("mp-2534")
rocksalt = mpr.get_structure_by_material_id("mp-22862")
perovskite = mpr.get_structure_by_material_id("mp-5827")
spinel_caco2s4 = mpr.get_structure_by_material_id("mvc-12728")
spinel_sicd2O4 = mpr.get_structure_by_material_id("mp-560842")

test = ASEFingerprint(
    perovskite.composition, on_fail=[], max_fails=[], initial_structures=[]
)

print(test.check_structure(perovskite))

##############################################################################

import time

from tqdm import tqdm

# I will record structure sizes and times into lists
num_sites = []
cnnf_times = []
rdff_times = []
prdff_times = []
pcnnf_times = []

# start with a [1,1,1] cell size
size = [
    0,
    1,
    1,
]  # because we start adding below - I have the first at 0, the first cycle will turn this into a 1

# we are going to try 10 different supercell sizes
for n in tqdm(range(10)):

    # reset the perovskite structure to its unitcell
    perovskite = mpr.get_structure_by_material_id("mp-5827")

    # change the supercell size
    # this line will make sizes increment by one in each axis (111, 211, 221, 222, 322, 332, ...)
    size[n % 3] += 1

    # use the size to make the pervoskite supercell
    perovskite.make_supercell(size)

    # append the cell size
    num_sites.append(perovskite.num_sites)

    ##### TEST METHOD 1 #####
    fpval = CrystalNNFingerprint(
        on_fail=[],
        max_fails=[],
        cnn_options={},
        stat_options=["mean", "std_dev", "minimum", "maximum"],
        initial_structures=[],
        parallel=False,
    )

    s = time.time()
    check1 = fpval.check_structure(perovskite)
    # check2 = fpval.check_structure(perovskite)
    e = time.time()
    cnnf_times.append(e - s)
    #########################

    ##### TEST METHOD 2 #####
    fpval2 = RDFFingerprint(on_fail=[], max_fails=[])

    s = time.time()
    check01 = fpval2.check_structure(perovskite)
    # check02 = fpval2.check_structure(perovskite)
    e = time.time()
    rdff_times.append(e - s)
    #########################

    ##### TEST METHOD 3 #####
    fpval3 = PartialRDFFingerprint(
        composition=perovskite.composition, on_fail=[], max_fails=[]
    )

    s = time.time()
    check001 = fpval3.check_structure(perovskite)
    # check002 = fpval3.check_structure(perovskite)
    e = time.time()
    prdff_times.append(e - s)
    #########################

    ##### TEST METHOD 4 #####
    fpval4 = PartialCrystalNNFingerprint(
        composition=perovskite.composition,
        on_fail=[],
        max_fails=[],
        cnn_options={},
        stat_options=["mean", "std_dev", "minimum", "maximum"],
        initial_structures=[],
        parallel=False,
    )

    s = time.time()
    check0001 = fpval4.check_structure(perovskite)
    # check0002 = fpval4.check_structure(perovskite)
    e = time.time()
    pcnnf_times.append(e - s)
    #########################


# Now let's plot the results

### IMPORT PLOTLY FUNCTIONS ###
import plotly.graph_objects as go
from plotly.offline import plot

series1 = go.Scatter(
    name="CrystalNNFingerprint",
    x=num_sites,
    y=cnnf_times,
    mode="lines+markers",
)

series2 = go.Scatter(
    name="RDFFingerprint",
    x=num_sites,
    y=rdff_times,
    mode="lines+markers",
)

series3 = go.Scatter(
    name="PartialRDFFingerprint",
    x=num_sites,
    y=prdff_times,
    mode="lines+markers",
)

series4 = go.Scatter(
    name="PartialCrystalNNFingerprint",
    x=num_sites,
    y=pcnnf_times,
    mode="lines+markers",
)

layout = go.Layout(
    width=800,
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(
        title_text="Cell Size (# sites)",
        # range=[2,5.2],
        showgrid=False,
        zeroline=False,
        ticks="outside",
        tickwidth=2,
        showline=True,
        color="black",
        linecolor="black",
        linewidth=2,
        mirror=True,
        # dtick=0.5,
        # tick0=1.75,
    ),
    yaxis=dict(
        title_text="Fingerprint Time (s)",
        # range=[-0.25,10],
        showgrid=False,
        zeroline=False,
        ticks="outside",
        tickwidth=2,
        showline=True,
        linewidth=2,
        color="black",
        linecolor="black",
        mirror=True,
        # dtick=2,
        # tick0=0,
    ),
    legend=dict(
        x=0.05,
        y=0.95,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    ),
)

fig = go.Figure(data=[series1, series2, series3, series4], layout=layout)

plot(fig, config={"scrollZoom": True})

#############################################################################
