# -*- coding: utf-8 -*-

# TESTING PARALLEL

# from dask.distributed import Client
# client = Client() #  processes=False

# from pymatdisc.core.creators.structure import RandomSymStructure
# from pymatgen.core.composition import Composition
# c = Composition('Al4O6')
# test = RandomSymStructure(c)

# import time
# s = time.time()
# x = test.create_structure(1)
# e = time.time()
# print(e-s)

# import time
# s = time.time()
# x = test.create_many_structures(200, 1, progressbar=True, mode='threads')
# e = time.time()
# print(e-s)

##############################################################################

# for progress monitoring and time recording
from tqdm import tqdm

# from time import time # incorrectly gives 0 seconds in some cases
from timeit import default_timer as time
import os


def time_test_struct_creation(creator, n):
    times = []
    for n in tqdm(range(n)):
        structure = False
        while not structure:
            start = time()
            structure = creator.create_structure()
            end = time()
        times.append(end - start)
        structure.to(fmt="cif", filename=str(n) + ".cif")
    return times


##############################################################################

# I'll store the data in these two variables
import pandas
import numpy

times_all = []
mapping = [
    "PyMatDisc"
]  # , 'ASE', 'GASP', 'PyXtal', 'XtalOpt', 'USPEX', 'CALYPSO', 'AIRSS'
n = 100

##############################################################################

# Establish the composition that we are testing.
# Here is a list of our control (reduced) compositions and the total atom
# counts for their known global minimum structures:
# Fe 1
# Si 2
# C 4
# TiO2 6
# SiO2 6
# Al2O3 10
# Si2N2O 10
# SrSiN2 16
# MgSiO3 20 and 40

from pymatgen.core.composition import Composition

compositions_strs = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    "Si4O8",
    "Al4O6",
]  # 'Si4N4O2', 'Sr4Si4N8', 'Mg4Si4O12', 'Mg8Si8O24'
compositions_objs = [Composition(c) for c in compositions_strs]

##############################################################################

### PYMATDISC

# Let's test PyMatDisc first, which we need the generator for (bc only the gen has the site distance check)
# !!! decide between with and without fingerprint check
from pymatdisc.core.creators.structure import RandomSymStructure

times_creator = []
os.mkdir("PyMatDisc")
os.chdir("PyMatDisc")
for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
    os.mkdir(comp_str)
    os.chdir(comp_str)
    creator = RandomSymStructure(comp_obj)
    times_comp = time_test_struct_creation(creator, n)
    os.chdir("..")
    times_creator.append(times_comp)
os.chdir("..")
times_all.append(times_creator)

df_pymatdisc = pandas.DataFrame(
    numpy.transpose(times_creator), columns=compositions_strs
)
df_pymatdisc.to_csv("PyMatDisc.csv")

##############################################################################

### ASE

# from pymatdisc.creators.structure import ASEStructure

# times_creator = []
# os.mkdir('ASE')
# os.chdir('ASE')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in ['Fe1']: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     creator = ASEStructure(comp_obj)
#     times_comp = time_test_struct_creation(creator, n)
#     os.chdir('..')
#     times_creator.append(times_comp)
# os.chdir('..')
# times_all.append(times_creator)

# df_ase = pandas.DataFrame(numpy.transpose(times_creator),
#                           columns=compositions_strs)
# df_ase.to_csv('ASE.csv')

##############################################################################

### GASP

# # from pymatdisc.creators.structure import GASPStructure
# from pymatdisc.generators.base import PrimaryGenerator

# times_creator = []
# os.mkdir('GASP')
# os.chdir('GASP')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in []: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     # creator = GASPStructure(comp_obj)
#     # times_comp = time_test_struct_creation(creator, n)
#     creator = PrimaryGenerator.from_preset('gasp', comp_obj)
#     times_comp = time_test_struct_generation(creator, n)
#     os.chdir('..')
#     times_creator.append(times_comp)
# os.chdir('..')
# times_all.append(times_creator)

# df_gasp = pandas.DataFrame(numpy.transpose(times_creator),
#                             columns=compositions_strs)
# df_gasp.to_csv('GASP.csv')

##############################################################################

### PyXtal

# from pymatdisc.creators.structure import PyXtalStructure

# times_creator = []
# os.mkdir('PyXtal')
# os.chdir('PyXtal')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in []: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     creator = PyXtalStructure(comp_obj)
#     times_comp = time_test_struct_creation(creator, n)
#     os.chdir('..')
#     times_creator.append(times_comp)
# os.chdir('..')
# times_all.append(times_creator)

# df_pyxtal = pandas.DataFrame(numpy.transpose(times_creator),
#                               columns=compositions_strs)
# df_pyxtal.to_csv('PyXtal.csv')

##############################################################################

### XtalOpt

# from pymatdisc.creators.structure import XtalOptStructure

# times_creator = []
# os.mkdir('XtalOpt')
# os.chdir('XtalOpt')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in []: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     creator = XtalOptStructure(comp_obj)
#     times_comp = time_test_struct_creation(creator, n)
#     os.chdir('..')
#     times_creator.append(times_comp)
# os.chdir('..')
# times_all.append(times_creator)

# df_xtalopt= pandas.DataFrame(numpy.transpose(times_creator),
#                               columns=compositions_strs)
# df_xtalopt.to_csv('XtalOpt.csv')

##############################################################################

### USPEX

# from pymatdisc.creators.structure import USPEXStructure

# times_creator = []
# os.mkdir('USPEX')
# os.chdir('USPEX')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in []: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     creator = USPEXStructure(comp_obj)
#     structures = creator.new_structures(n)
#     for i, structure in enumerate(structures):
#         structure.to(fmt='cif', filename=str(i) + '.cif')
#     os.chdir('..')
#     times_creator.append([]) #!!! cant timetest yet
# os.chdir('..')
# times_all.append(times_creator)

##############################################################################

### CALYPSO

# from pymatdisc.creators.structure import CALYPSOStructure

# times_creator = []
# os.mkdir('CALYPSO')
# os.chdir('CALYPSO')
# for comp_str, comp_obj in zip(compositions_strs, compositions_objs):
#     if comp_str in []: # Fails with...
#         times_creator.append([None]*n)
#         continue
#     os.mkdir(comp_str)
#     os.chdir(comp_str)
#     creator = CALYPSOStructure(comp_obj)
#     structures = creator.new_structures(n)
#     for i, structure in enumerate(structures):
#         structure.to(fmt='cif', filename=str(i) + '.cif')
#     os.chdir('..')
#     times_creator.append([]) #!!! cant timetest yet
# os.chdir('..')
# times_all.append(times_creator)

##############################################################################

### Plotting Timetest

import pandas

dfs = []
for name in mapping:
    df = pandas.read_csv("{}.csv".format(name), index_col=0)
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
        xs += [c] * n

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
        title_text="Time to Generate Single Structure (s)",
        type="log",
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

##############################################################################
##############################################################################
##############################################################################
##############################################################################

### Fingerprint Comparison

# import os
# import numpy as np
# import itertools
# from pymatgen.core.structure import Structure

# from matminer.featurizers.site import CrystalNNFingerprint as cnnf
# sitefingerprint_method = cnnf.from_preset('ops', distance_cutoffs=None, x_diff_weight=3)

# from pymatdisc.validators.fingerprint import PartialsSiteStatsFingerprint #!!! this should move to matminer
# featurizer = PartialsSiteStatsFingerprint(sitefingerprint_method,
#                                           stats=['mean', 'std_dev', 'minimum', 'maximum'])

# # this is the total number of comparisons to be made
# n_combos = len([1 for combo in itertools.combinations(range(n), 2)])
# limit = 1000

# # store all the distances here
# distances_all = []

# # iterate through the creator folders
# for name in mapping:
#     os.chdir(name)
#     # pick the composition
#     distances_creator = []
#     for comp_str, comp_obj in tqdm(zip(compositions_strs, compositions_objs)):
#         if comp_str in ['Fe1'] and name == 'ASE': # Fails with...
#             distances_creator.append([None]*limit) #!!!
#             continue
#         os.chdir(comp_str)
#         # fitting of the featurizer to the composition
#         featurizer.elements_ = np.array([element.symbol for element in comp_obj.elements])
#         # load the cifs
#         structures = [Structure.from_file('{}.cif'.format(i), primitive=True) for i in range(n)]
#         # calculate the fingerprint (in parallel)
#         fingerprints = featurizer.featurize_many(structures, pbar=False)
#         # calculate the distances for all combinations of structures
#         distances_comp = [np.linalg.norm(combo[0] - combo[1]) for combo in itertools.combinations(fingerprints, 2)]
#         if limit:
#             distances_comp = np.random.choice(distances_comp, limit, replace=False)
#         # add to ouput
#         distances_creator.append(distances_comp)
#         # move back to main directory
#         os.chdir('..')
#     os.chdir('..')
#     distances_all.append(distances_creator)

#     df = pandas.DataFrame(numpy.transpose(distances_creator),
#                           columns=compositions_strs)
#     df.to_csv('{}_distances.csv'.format(name))

##############################################################################

### Plotting DistanceTest

# import pandas
# dfs = []
# for name in mapping:
#     df = pandas.read_csv('{}_distances.csv'.format(name), index_col=0)
#     dfs.append(df)

# import plotly.graph_objects as go
# from plotly.offline import plot

# composition_strs = ['Fe1', 'Si2', 'C4', 'Ti2O4', 'Si4O8', 'Al4O6', 'Si4N4O2', 'Sr4Si4N8', 'Mg4Si4O12', 'Mg8Si8O24']

# data = []

# for name, df in zip(mapping, dfs):
#     # y should be all time values for ALL compositions put together in to a 1D array
#     ys = df.values.flatten(order='F')
#     # x should be labels that are the same length as the xs list
#     xs = []
#     for c in composition_strs:
#         xs += [c] * limit #!!!

#     series = go.Box(name=name,
#                     x=xs,
#                     y=ys,
#                     boxpoints= False, # look at strip plots if you want the scatter points
#                     )
#     data.append(series)


# layout = go.Layout(width=800,
#                     height=600,
#                     plot_bgcolor='white',
#                     paper_bgcolor='white',
#                     boxmode='group',
#                     xaxis=dict(title_text='Composition',
#                                   showgrid=False,
#                                   ticks='outside',
#                                   tickwidth=2,
#                                   showline=True,
#                                   color='black',
#                                   linecolor='black',
#                                   linewidth=2,
#                                   mirror=True,
#                                   ),
#                     yaxis=dict(title_text='Distance Between Fingerprints',
#                               # type="log",
#                               ticks='outside',
#                               tickwidth=2,
#                               showline=True,
#                               linewidth=2,
#                               color='black',
#                               linecolor='black',
#                               mirror=True,
#                               ),
#                     legend=dict(x=0.05,
#                                 y=0.95,
#                                 bordercolor='black',
#                                 borderwidth=1,
#                                 font=dict(color='black'),
#                                 ),
#                     )

# fig = go.Figure(data=data,
#                 layout=layout
#                 )

# plot(fig, config={'scrollZoom': True})

##############################################################################
##############################################################################
##############################################################################
##############################################################################
