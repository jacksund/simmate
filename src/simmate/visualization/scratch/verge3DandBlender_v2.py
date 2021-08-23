#####################################################

from pymatgen.ext.matproj import MPRester
import numpy as np
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator, CrystalNN
import itertools as it

mpr = MPRester("2Tg7uUvaTAPHJQXl")

# 1078631 # 1206889 # 2686 # 661 # 1228939
mp_id = "mp-661"  # change this to your material of interest
structure = mpr.get_structure_by_material_id(
    mp_id, conventional_unit_cell=False
)  # , conventional_unit_cell=True
structure = structure.copy(sanitize=True)
# structure.make_supercell(2)

# run oxidation analysis and predict bonding
structure = ValenceIonicRadiusEvaluator(structure).structure
structure_graph = CrystalNN().get_bonded_structure(structure)

# grab base sites and lattice
sites = structure.sites
lattice = structure.lattice.matrix

# gather all site coords (cart.) that we want to display
sites_to_draw = []
for site in sites:
    element = site.specie.element.symbol  # .long_name
    radius = (
        site.specie.ionic_radius
    )  # sometimes returns None...? can get around this with ValenceIonicRadiusEvaluator(structure).radii[site.species_string]
    if type(radius) == type(
        None
    ):  # to catch bug where ValenceIonicRadiusElavulator does assign a radius
        radius = 0.75
    coords = np.dot(site.frac_coords, lattice)
    sites_to_draw.append((element, radius, coords.tolist()))
    # duplicate along edges
    ## for sites that have a 0 element
    zero_elements = [
        i for i, x in enumerate(site.frac_coords) if np.isclose(x, 0, atol=0.05)
    ]
    permutatons = [
        combination
        for n in range(1, len(zero_elements) + 1)
        for combination in it.combinations(zero_elements, n)
    ]
    for p in permutatons:
        shift_vector = np.zeros(3)
        for i in p:
            shift_vector = np.add(shift_vector, lattice[i])
        new_coords = np.add(coords, shift_vector)
        sites_to_draw.append((element, radius, new_coords.tolist()))
    ## for sites that have a 1 element
    one_elements = [
        i for i, x in enumerate(site.frac_coords) if np.isclose(x, 1, atol=0.05)
    ]
    permutatons = [
        combination
        for n in range(1, len(one_elements) + 1)
        for combination in it.combinations(one_elements, n)
    ]
    for p in permutatons:
        shift_vector = np.zeros(3)
        for i in p:
            shift_vector = np.add(shift_vector, lattice[i])
        new_coords = np.subtract(coords, shift_vector)
        sites_to_draw.append((element, radius, new_coords.tolist()))

## Add bonded sites outside of unticell
### Two issues exist for this code:
#### 1. doesn't find bonded sites to atoms that were duplicated along edges
#### 2. duplicate atoms are added to sites_to_draw
# for n in range(len(structure_graph.structure)):
#    connected_sites = structure_graph.get_connected_sites(n)
#    for connected_site in connected_sites:
#        if connected_site.jimage != (0, 0, 0):
#            sites_to_draw.append(connected_site.site.coords)


#####################################################

import json

path_to_script = "C:/Users/jacks/Anaconda3/envs/jacks_env/Lib/site-packages/jacksund/WarrenLabToolBox/Other/background_blender.py"
sites_to_draw = json.dumps(sites_to_draw).replace('"', "'")
lattice = json.dumps(lattice.tolist())
save = "C:/Users/jacks/Desktop/test"
command_base = 'blender --background --factory-startup --python {} -- --sites="{}" --lattice="{}" --save="{}"'
command_final = command_base.format(path_to_script, sites_to_draw, lattice, save)

import os

os.system(command_final)


#####################################################
