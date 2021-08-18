#####################################################

from pymatgen import MPRester
import numpy as np
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator, CrystalNN
import itertools as it

mpr = MPRester("2Tg7uUvaTAPHJQXl")

mp_id = "mp-22936"  # change this to your material of interest
structure = mpr.get_structure_by_material_id(
    mp_id, conventional_unit_cell=False
)  # , conventional_unit_cell=True
# structure = structure.copy(sanitize=True)
# structure.make_supercell(2)

# run oxidation analysis and predict bonding
structure = ValenceIonicRadiusEvaluator(structure).structure
structure_graph = CrystalNN().get_bonded_structure(structure)

# grab base sites and lattice
sites = structure.frac_coords
lattice = structure.lattice.matrix

# gather all site coords (cart.) that we want to display
sites_to_draw = []
for site in sites:
    coords = np.dot(site, lattice)
    sites_to_draw.append(coords)
    # duplicate along edges
    ## for sites that have a 0 element
    zero_elements = [i for i, x in enumerate(site) if np.isclose(x, 0, atol=0.05)]
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
        sites_to_draw.append(new_coords)
    ## for sites that have a 1 element
    one_elements = [i for i, x in enumerate(site) if np.isclose(x, 1, atol=0.05)]
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
        sites_to_draw.append(new_coords)

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

import bpy

# delete starting enviornment
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

for coords in sites_to_draw:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, size=0.75, location=coords)

# make smooth shading for all then deselect
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.shade_smooth()
bpy.ops.object.select_all(action="SELECT")

# Add lattice
bpy.ops.mesh.primitive_cube_add(radius=1, enter_editmode=True)
bpy.ops.mesh.delete(type="ONLY_FACE")
bpy.ops.object.editmode_toggle()
verts = bpy.context.object.data.vertices
verts[0].co = (0, 0, 0)
verts[1].co = lattice[2]
verts[2].co = lattice[0]
verts[3].co = np.add(lattice[0], lattice[2])
verts[4].co = lattice[1]
verts[5].co = np.add(lattice[1], lattice[2])
verts[6].co = np.add(lattice[0], lattice[1])
verts[7].co = np.sum(lattice, axis=0)
bpy.ops.object.convert(target="CURVE")
bpy.context.object.data.fill_mode = "FULL"
bpy.context.object.data.bevel_depth = 0.1
bpy.context.object.data.bevel_resolution = 0
bpy.context.object.data.bevel_resolution = 3
bpy.ops.object.shade_smooth()

# save file
bpy.ops.wm.save_as_mainfile(filepath="testing.blend")
