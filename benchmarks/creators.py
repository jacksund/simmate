# -*- coding: utf-8 -*-

import logging
from timeit import default_timer as time

import numpy
import pandas
from rich.progress import track

from simmate.toolkit import Composition
from simmate.utilities import get_directory

# BUG: from time import time --> incorrectly gives 0 seconds in some cases, so
# therefore use the timeit module instead

# Disable logging throughout for cleaner output
logger = logging.getLogger()
logger.disabled = True

# Establish the compositions and settings that we are testing.
# Here is a list of our control (reduced) compositions and the total atom
# counts for their known global minimum structures:
COMPOSITIONS_TO_TEST = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    # "Si4O8",
    # "Al4O6",
    # "Si4N4O2",
    # "Sr4Si4N8",
    # "Mg4Si4O12",
]

NSAMPLES_PER_COMPOSITION = 50


def time_test_creation(creator_class, creator_kwargs):

    compositions = [Composition(c) for c in COMPOSITIONS_TO_TEST]

    directory = get_directory(creator_class.name)

    all_comp_times = []

    for composition in compositions:

        # BUG: some creators fail for specific compositions
        if str(composition) == "Fe1" and creator_class.name == "AseStructure":
            all_comp_times.append([None] * NSAMPLES_PER_COMPOSITION)
            continue

        comp_directory = get_directory(directory / str(composition))

        creator = creator_class(composition, **creator_kwargs)

        single_comp_times = []
        for n in track(
            range(NSAMPLES_PER_COMPOSITION),
            description=f"{creator_class.name} - {composition}",
        ):
            structure = False
            attempt = 1
            while not structure:
                attempt += 1
                start = time()
                structure = creator.create_structure()
                end = time()
            single_comp_times.append(end - start)
            structure.to(
                fmt="cif",
                filename=comp_directory / f"{n}.cif",
            )
        all_comp_times.append(single_comp_times)

    df = pandas.DataFrame(
        numpy.transpose(all_comp_times),
        columns=COMPOSITIONS_TO_TEST,
    )
    # df.to_csv(f"{creator_class.name}.csv")

    # attach data for future reference
    creator_class.benchmark_results = df

    return df


# -----------------------------------------------------------------------------

from simmate.toolkit.creators.structure.random_symmetry import RandomSymStructure
from simmate.toolkit.creators.structure.third_party.ase import AseStructure
from simmate.toolkit.creators.structure.third_party.gasp import GaspStructure
from simmate.toolkit.creators.structure.third_party.pyxtal import PyXtalStructure
from simmate.toolkit.creators.structure.third_party.xtalopt import XtaloptStructure

CREATORS_TO_TEST = [
    (
        RandomSymStructure,
        {
            "site_gen_options": {
                "lazily_generate_combinations": False,
            }
        },
    ),
    (AseStructure, {}),
    (PyXtalStructure, {}),
    (GaspStructure, {}),
    (
        XtaloptStructure,
        {
            "command": "/home/jacksund/Documents/github/randSpg/build/randSpg",
        },
    ),
]
for creator_class, creator_kwargs in CREATORS_TO_TEST:
    time_test_creation(creator_class, creator_kwargs)

# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------

### Plotting Timetest

import plotly.graph_objects as go
from plotly.offline import plot

data = []

for creator, _ in CREATORS_TO_TEST:
    # y should be all time values for ALL compositions put together in to a 1D array
    ys = creator.benchmark_results.values.flatten(order="F")
    # x should be labels that are the same length as the xs list
    xs = []
    for c in COMPOSITIONS_TO_TEST:
        xs += [c] * NSAMPLES_PER_COMPOSITION

    series = go.Box(
        name=creator.name,
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

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

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
#     for comp_str, comp_obj in track(zip(compositions_strs, compositions_objs)):
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

# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
