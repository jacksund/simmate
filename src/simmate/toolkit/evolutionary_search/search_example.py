# -*- coding: utf-8 -*-

from pymatdisc.engine.search import Search  #!!! Need to move this

######### EXAMPLE RUN ###########

composition = "Si4N4O2"  # for EMT, stick to Al, Ni, Cu, Pd, Ag, Pt and Au.

# from pymatdisc.core.transformations.all import CoordinatePerturbationASE #!!! example of a custom import
# sources = [(0.20, 'RandomSymStructure', {'spacegroup_include': range(1,231),
#                                           'spacegroup_exclude': [],
#                                           'lattice_generation_method': 'RSLSmartVolume',
#                                           'lattice_gen_options': {'angle_generation_method': 'UniformlyDistributedVectors'},
#                                           'site_generation_method': 'RandomWySites',
#                                           'site_gen_options': {},}), #!!! example of setting custom method
#             (0.50, 'HeredityASE', {}),
#             (0.10, 'SoftMutationASE', {}),
#             (0.05, 'MirrorMutationASE', {}),
#             (0.05, 'LatticeStrainASE', {}),
#             (0.05, 'RotationalMutationASE', {}),
#             (0.025, 'AtomicPermutationASE', {}),
#             (0.025, CoordinatePerturbationASE, {}), #!!! example of a custom import
#             ]

# analysis = ('PrefectLocal', {})

# triggers = [('InitStructures', {'n_initial_structures': 15}),
#             ('AddStructures', {'n_pending_limit':5,
#                                 'n_add_structures':15,}),
#             ]

# stop_condition = ('BasicStopConditions', {})


search = Search(
    composition=composition,
    # sources = sources,
    # analysis = analysis,
    # triggers = triggers,
    # stop_condition = stop_condition,
)

search.run()

####################################################################

######### TO-DO ###########

"""

visualization / plotting / workup

search exits when I hit the structure limit -- I should wait until all submitted structures finish

restrict RandomSymStructure to the target nsites -- Symmetry sometimes returns fewer

consider making the in-memory database a pandas dataframe or Sample objects

Continue calc from previous csv/cifs

add database class that links to Postgres cloud (via sqlalchemy or django)

custom starting structures

fingerprinting -- inside Selector class?

"archive" structures -- remove them from the list of search.structures if they no longer have a
chance to be selected. This will help with the memory load for longer searches. 

update prefect workflow to multistep

multistep workflow have cutoffs as in input parameter...? This would be much 
easier than making a query - maybe future version can do that.

"""

####################################################################


# from pymatgen import MPRester
# mpr = MPRester('2Tg7uUvaTAPHJQXl')
# structure = mpr.get_structure_by_material_id('mp-23')
