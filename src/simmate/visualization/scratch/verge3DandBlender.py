#####################################################

import sys
import os
# turn off printing
sys.stdout = open(os.devnull, 'w')

#####################################################

jmol_coloring = {'H': [255,255,255],
                 'He': [217,255,255],
                 'Li': [204,128,255],
                 'Be': [194,255,0],
                 'B': [255,181,181],
                 'C': [144,144,144],
                 'N': [48,80,248],
                 'O': [255,13,13],
                 'F': [144,224,80],
                 'Ne': [179,227,245],
                 'Na': [171,92,242],
                 'Mg': [138,255,0],
                 'Al': [191,166,166],
                 'Si': [240,200,160],
                 'P': [255,128,0],
                 'S': [255,255,48],
                 'Cl': [31,240,31],
                 'Ar': [128,209,227],
                 'K': [143,64,212],
                 'Ca': [61,255,0],
                 'Sc': [230,230,230],
                 'Ti': [191,194,199],
                 'V': [166,166,171],
                 'Cr': [138,153,199],
                 'Mn': [156,122,199],
                 'Fe': [224,102,51],
                 'Co': [240,144,160],
                 'Ni': [80,208,80],
                 'Cu': [200,128,51],
                 'Zn': [125,128,176],
                 'Ga': [194,143,143],
                 'Ge': [102,143,143],
                 'As': [189,128,227],
                 'Se': [255,161,0],
                 'Br': [166,41,41],
                 'Kr': [92,184,209],
                 'Rb': [112,46,176],
                 'Sr': [0,255,0],
                 'Y': [148,255,255],
                 'Zr': [148,224,224],
                 'Nb': [115,194,201],
                 'Mo': [84,181,181],
                 'Tc': [59,158,158],
                 'Ru': [36,143,143],
                 'Rh': [10,125,140],
                 'Pd': [0,105,133],
                 'Ag': [192,192,192],
                 'Cd': [255,217,143],
                 'In': [166,117,115],
                 'Sn': [102,128,128],
                 'Sb': [158,99,181],
                 'Te': [212,122,0],
                 'I': [148,0,148],
                 'Xe': [66,158,176],
                 'Cs': [87,23,143],
                 'Ba': [0,201,0],
                 'La': [112,212,255],
                 'Ce': [255,255,199],
                 'Pr': [217,255,199],
                 'Nd': [199,255,199],
                 'Pm': [163,255,199],
                 'Sm': [143,255,199],
                 'Eu': [97,255,199],
                 'Gd': [69,255,199],
                 'Tb': [48,255,199],
                 'Dy': [31,255,199],
                 'Ho': [0,255,156],
                 'Er': [0,230,117],
                 'Tm': [0,212,82],
                 'Yb': [0,191,56],
                 'Lu': [0,171,36],
                 'Hf': [77,194,255],
                 'Ta': [77,166,255],
                 'W': [33,148,214],
                 'Re': [38,125,171],
                 'Os': [38,102,150],
                 'Ir': [23,84,135],
                 'Pt': [208,208,224],
                 'Au': [255,209,35],
                 'Hg': [184,184,208],
                 'Tl': [166,84,77],
                 'Pb': [87,89,97],
                 'Bi': [158,79,181],
                 'Po': [171,92,0],
                 'At': [117,79,69],
                 'Rn': [66,130,150],
                 'Fr': [66,0,102],
                 'Ra': [0,125,0],
                 'Ac': [112,171,250],
                 'Th': [0,186,255],
                 'Pa': [0,161,255],
                 'U': [0,143,255],
                 'Np': [0,128,255],
                 'Pu': [0,107,255],
                 'Am': [84,92,242],
                 'Cm': [120,92,227],
                 'Bk': [138,79,227],
                 'Cf': [161,54,212],
                 'Es': [179,31,212],
                 'Fm': [179,31,186],
                 'Md': [179,13,166],
                 'No': [189,13,135],
                 'Lr': [199,0,102],
                 'Rf': [204,0,89],
                 'Db': [209,0,79],
                 'Sg': [217,0,69],
                 'Bh': [224,0,56],
                 'Hs': [230,0,46],
                 'Mt': [235,0,38]}

# to add 4th value for blender
for key in jmol_coloring:
    jmol_coloring[key].append(255)

#####################################################

from pymatgen import MPRester
import numpy as np
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator, CrystalNN
import itertools as it

mpr = MPRester("2Tg7uUvaTAPHJQXl")

# 1078631 # 1206889
mp_id =  "mp-1078631" # change this to your material of interest 
structure = mpr.get_structure_by_material_id(mp_id, conventional_unit_cell=False) #, conventional_unit_cell=True
structure = structure.copy(sanitize=True)
structure.make_supercell(2)

# run oxidation analysis and predict bonding
structure = ValenceIonicRadiusEvaluator(structure).structure
structure_graph = CrystalNN().get_bonded_structure(structure)

# grab base sites and lattice
sites = structure.sites
lattice = structure.lattice.matrix

# gather all site coords (cart.) that we want to display
sites_to_draw = []
for site in sites:
    element = site.specie.element.symbol # .long_name
    radius = site.specie.ionic_radius # sometimes returns None...? can get around this with ValenceIonicRadiusEvaluator(structure).radii[site.species_string]
    coords = np.dot(site.frac_coords,lattice)
    sites_to_draw.append((element, radius, coords))
    # duplicate along edges
    ## for sites that have a 0 element
    zero_elements = [i for i, x in enumerate(site.frac_coords) if np.isclose(x, 0, atol=0.05)]
    permutatons = [combination 
                   for n in range(1, len(zero_elements) + 1) 
                   for combination in it.combinations(zero_elements, n)]
    for p in permutatons:
        shift_vector = np.zeros(3)
        for i in p:
            shift_vector = np.add(shift_vector, lattice[i])
        new_coords = np.add(coords, shift_vector)
        sites_to_draw.append((element, radius, new_coords))
    ## for sites that have a 1 element
    one_elements = [i
                    for i, x in enumerate(site.frac_coords) 
                    if np.isclose(x, 1, atol=0.05)]
    permutatons = [combination 
                   for n in range(1, len(one_elements) + 1) 
                   for combination in it.combinations(one_elements, n)]
    for p in permutatons:
        shift_vector = np.zeros(3)
        for i in p:
            shift_vector = np.add(shift_vector, lattice[i])
        new_coords = np.subtract(coords, shift_vector)
        sites_to_draw.append((element, radius, new_coords))
        
## Add bonded sites outside of unticell
### Two issues exist for this code:
#### 1. doesn't find bonded sites to atoms that were duplicated along edges
#### 2. duplicate atoms are added to sites_to_draw
#for n in range(len(structure_graph.structure)):
#    connected_sites = structure_graph.get_connected_sites(n)
#    for connected_site in connected_sites:
#        if connected_site.jimage != (0, 0, 0):
#            sites_to_draw.append(connected_site.site.coords)

#####################################################

import bpy
import addon_utils

#addon_utils.enable(module_name="verge3d")

## make world color white
#bpy.data.worlds['World'].color = (1, 1, 1) # blender 2.79 uses .ambient_color

# delete starting enviornment
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

for site in sites_to_draw:
    site_element, site_size, site_loc = site
    site_color = np.array(jmol_coloring[site_element]) / 255 # divide each value by 255 to standardize for blender
    if type(site_size) == type(None): # to catch bug
        site_size = 0.75 
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=site_size, location=site_loc) # creates and sets to active object
    
    # make material for new object
    mat = bpy.data.materials.new(name="test-material") # create material
    mat.diffuse_color = site_color
    bpy.context.active_object.data.materials.append(mat) # append material to selected objects

# make smooth shading for all then deselect
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.shade_smooth()
bpy.ops.object.select_all(action='DESELECT')

# Add lattice # ISSUE WHERE EACH LINE ISNT PERFECT CIRCLE >>> WILL FIX BY SEPARATING LINES
bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=True)
bpy.ops.mesh.delete(type='ONLY_FACE')
bpy.ops.object.editmode_toggle()

verts = bpy.context.object.data.vertices
verts[0].co = (0,0,0)
verts[1].co = lattice[2]
verts[2].co = lattice[0]
verts[3].co = np.add(lattice[0],lattice[2])
verts[4].co = lattice[1]
verts[5].co = np.add(lattice[1],lattice[2])
verts[6].co = np.add(lattice[0],lattice[1])
verts[7].co = np.sum(lattice, axis=0)

# Split edges, which requires the bmesh module
#bpy.ops.mesh.edge_split() # doesn't work because of context/poll check
import bmesh as bmesh
lattice = bpy.data.objects[0].data # regular bpy object
bm = bmesh.new() # create new bmesh
bm.from_mesh(lattice) # fill bmesh with data from bpy object
bmesh.ops.split_edges(bm, edges=bm.edges) # spit the edges on the mesh
bm.to_mesh(lattice) # write the result data back to the initial bpy object

bpy.ops.object.convert(target='CURVE')
bpy.context.object.data.fill_mode = 'FULL'
bpy.context.object.data.bevel_depth = 0.1
bpy.context.object.data.bevel_resolution = 0
bpy.context.object.data.bevel_resolution = 3
bpy.ops.object.shade_smooth()

#make lattice black
mat = bpy.data.materials.new(name="Test-Material") # create material # can be grabbed later with bpy.data.materials['Test-Material']
mat.diffuse_color = (0, 0, 0, 0) # make black
mat.specular_intensity = 0 # turn of specular
bpy.context.active_object.data.materials.append(mat) # append material to selected objects

# set lattice origin to geometry (so we can set camera to lattice center)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

# add camera
bpy.ops.object.camera_add(location=(0, 0, 0), rotation=(0, 0, 0))

# add sun
bpy.ops.object.light_add(type='SUN', radius=1, location=(0, 0, 0))

## Center all objects at the origin  # fails as-is. consider centering camera to lattice
#bpy.ops.object.select_all(action='SELECT')
#bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

## scale the whole crystal structure
#bpy.ops.object.select_all(action='SELECT')
#bpy.ops.transform.resize(value=(1.29349, 1.29349, 1.29349))

# save file
bpy.ops.wm.save_as_mainfile(filepath='/home/jacksund/Documents/Spyder/testing.blend')

# export for Verge3D
#bpy.context.scene.v3d_export.lzma_enabled = True # add compressed files (fails for some reason)
#bpy.ops.export_scene.v3d_gltf(filepath="C:/Users/jacks/Desktop/Spyder_WorkDir/testing")

#####################################################

## list/collection of all objects 
#bpy.data.objects
#
## (de-)select object by name
#bpy.data.objects['Cube'].select_set(True) # or False
#
## (de-)select all objects
#bpy.ops.object.select_all(action='SELECT') # or 'DESELECT'
#
## delete selected objects
#bpy.ops.object.delete()

# open a file
#bpy.ops.wm.open_mainfile(filepath="C:/Users/jacks/Desktop/Spyder_WorkDir/testing.blend")

#####################################################










