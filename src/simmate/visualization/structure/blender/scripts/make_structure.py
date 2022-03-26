# -*- coding: utf-8 -*-

import json
import sys
import argparse

import numpy

import bpy
import bmesh

# These are the RGB values that JMol uses to color atoms
JMOL_COLORING = {
    "H": [255, 255, 255],
    "He": [217, 255, 255],
    "Li": [204, 128, 255],
    "Be": [194, 255, 0],
    "B": [255, 181, 181],
    "C": [144, 144, 144],
    "N": [48, 80, 248],
    "O": [255, 13, 13],
    "F": [144, 224, 80],
    "Ne": [179, 227, 245],
    "Na": [171, 92, 242],
    "Mg": [138, 255, 0],
    "Al": [191, 166, 166],
    "Si": [240, 200, 160],
    "P": [255, 128, 0],
    "S": [255, 255, 48],
    "Cl": [31, 240, 31],
    "Ar": [128, 209, 227],
    "K": [143, 64, 212],
    "Ca": [61, 255, 0],
    "Sc": [230, 230, 230],
    "Ti": [191, 194, 199],
    "V": [166, 166, 171],
    "Cr": [138, 153, 199],
    "Mn": [156, 122, 199],
    "Fe": [224, 102, 51],
    "Co": [240, 144, 160],
    "Ni": [80, 208, 80],
    "Cu": [200, 128, 51],
    "Zn": [125, 128, 176],
    "Ga": [194, 143, 143],
    "Ge": [102, 143, 143],
    "As": [189, 128, 227],
    "Se": [255, 161, 0],
    "Br": [166, 41, 41],
    "Kr": [92, 184, 209],
    "Rb": [112, 46, 176],
    "Sr": [0, 255, 0],
    "Y": [148, 255, 255],
    "Zr": [148, 224, 224],
    "Nb": [115, 194, 201],
    "Mo": [84, 181, 181],
    "Tc": [59, 158, 158],
    "Ru": [36, 143, 143],
    "Rh": [10, 125, 140],
    "Pd": [0, 105, 133],
    "Ag": [192, 192, 192],
    "Cd": [255, 217, 143],
    "In": [166, 117, 115],
    "Sn": [102, 128, 128],
    "Sb": [158, 99, 181],
    "Te": [212, 122, 0],
    "I": [148, 0, 148],
    "Xe": [66, 158, 176],
    "Cs": [87, 23, 143],
    "Ba": [0, 201, 0],
    "La": [112, 212, 255],
    "Ce": [255, 255, 199],
    "Pr": [217, 255, 199],
    "Nd": [199, 255, 199],
    "Pm": [163, 255, 199],
    "Sm": [143, 255, 199],
    "Eu": [97, 255, 199],
    "Gd": [69, 255, 199],
    "Tb": [48, 255, 199],
    "Dy": [31, 255, 199],
    "Ho": [0, 255, 156],
    "Er": [0, 230, 117],
    "Tm": [0, 212, 82],
    "Yb": [0, 191, 56],
    "Lu": [0, 171, 36],
    "Hf": [77, 194, 255],
    "Ta": [77, 166, 255],
    "W": [33, 148, 214],
    "Re": [38, 125, 171],
    "Os": [38, 102, 150],
    "Ir": [23, 84, 135],
    "Pt": [208, 208, 224],
    "Au": [255, 209, 35],
    "Hg": [184, 184, 208],
    "Tl": [166, 84, 77],
    "Pb": [87, 89, 97],
    "Bi": [158, 79, 181],
    "Po": [171, 92, 0],
    "At": [117, 79, 69],
    "Rn": [66, 130, 150],
    "Fr": [66, 0, 102],
    "Ra": [0, 125, 0],
    "Ac": [112, 171, 250],
    "Th": [0, 186, 255],
    "Pa": [0, 161, 255],
    "U": [0, 143, 255],
    "Np": [0, 128, 255],
    "Pu": [0, 107, 255],
    "Am": [84, 92, 242],
    "Cm": [120, 92, 227],
    "Bk": [138, 79, 227],
    "Cf": [161, 54, 212],
    "Es": [179, 31, 212],
    "Fm": [179, 31, 186],
    "Md": [179, 13, 166],
    "No": [189, 13, 135],
    "Lr": [199, 0, 102],
    "Rf": [204, 0, 89],
    "Db": [209, 0, 79],
    "Sg": [217, 0, 69],
    "Bh": [224, 0, 56],
    "Hs": [230, 0, 46],
    "Mt": [235, 0, 38],
}

# Blender needs a 4th value for the opacity in addition to the RGB values given
# above. For all materials, we use 255 and append this to all of them here. Blender
# needs these values on a 0-1 scale instead of the 0-255. We address
# this below by dividing all values by 255
for key in JMOL_COLORING:
    color = JMOL_COLORING[key]
    color.append(255)
    JMOL_COLORING[key] = numpy.array(color) / 255


def make_structure_blend(lattice, sites_to_draw, filename):

    # convert variable from json str to original format
    lattice = json.loads(lattice)
    sites_to_draw = json.loads(sites_to_draw.replace("'", '"'))

    # import Verge3D settings
    # import addon_utils
    # addon_utils.enable(module_name="verge3d")

    # Clear existing objects.
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # we grab the entire blender scene for reference as it let's us access
    # all objects later
    scene = bpy.context.scene

    # -------------------------------------------------------------------------

    # ADDING THE SITES

    # We start by drawing each of the sites -- which is just a colored sphere
    # at the proper coordinates
    for site in sites_to_draw:

        # first pull the base information out of the serialized tuple
        element_symbol, radius, cartesian_coords = site

        # we change the coordinates into a numpy array for functionality
        cartesian_coords = numpy.array(cartesian_coords)

        # Add a sphere for the site. Note we make the radius size only 0.75% its
        # true size in order to help with visualization.
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=3,
            radius=radius * 0.75,
            location=cartesian_coords,
        )

        # Now we need to color and style the sphere.

        # grab the site color from our mappings above
        site_color = JMOL_COLORING[element_symbol]

        # first check if we have made this material already (i.e. an element of
        # this type has been made before). If so, we use that one.
        materials = bpy.data.materials
        if element_symbol in materials.keys():
            mat = materials[element_symbol]
        # otherwise we make a new material and name it after the element for
        # future reference.
        else:
            mat = bpy.data.materials.new(name=element_symbol)
            mat.diffuse_color = site_color
            mat.metallic = 1
            mat.specular_intensity = 0
            mat.roughness = 0.6
        # Now that we have the proper material create/selected, we can now
        # apply it to our sphere
        bpy.context.active_object.data.materials.append(mat)

    # We apply smooth shading to all the spheres and then deselect them before
    # moving on to the next step
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action="DESELECT")

    # -------------------------------------------------------------------------

    # ADDING THE LATTICE

    # We make a lattice by creating a cube, deleting all of the faces, and then
    # manually placing each of its verticies to match the lattice size.
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=True)
    bpy.ops.mesh.delete(type="ONLY_FACE")
    bpy.ops.object.editmode_toggle()
    verts = bpy.context.object.data.vertices
    verts[0].co = (0, 0, 0)
    verts[1].co = lattice[2]
    verts[2].co = lattice[0]
    verts[3].co = numpy.add(lattice[0], lattice[2])
    verts[4].co = lattice[1]
    verts[5].co = numpy.add(lattice[1], lattice[2])
    verts[6].co = numpy.add(lattice[0], lattice[1])
    verts[7].co = numpy.sum(lattice, axis=0)

    # There's an issue where each lattice edge isn't a perfect line. To fix
    # this, we split the cube into separate lines and make sure each of those
    # are "full curves" which is really just a cylinder.

    # This is the easy want to do this with the UI but we get an error here...
    # bpy.ops.mesh.edge_split() # doesn't work because of context/poll check
    lattice = bpy.data.objects[0].data  # regular bpy object
    bm = bmesh.new()  # create new bmesh
    bm.from_mesh(lattice)  # fill bmesh with data from bpy object
    bmesh.ops.split_edges(bm, edges=bm.edges)  # spit the edges on the mesh
    bm.to_mesh(lattice)  # write the result data back to the initial bpy object

    # now fill each vector to a given size
    bpy.ops.object.convert(target="CURVE")
    bpy.context.object.data.fill_mode = "FULL"
    bpy.context.object.data.bevel_depth = 0.1
    bpy.context.object.data.bevel_resolution = 3
    bpy.ops.object.shade_smooth()

    # Now we create a black material to color the lattice with
    mat = bpy.data.materials.new(name="Lattice")
    mat.diffuse_color = (0, 0, 0, 1)
    mat.specular_intensity = 0
    bpy.context.active_object.data.materials.append(mat)

    # -------------------------------------------------------------------------

    # CENTERING ALL OBJECTS

    # When we created all the objects above, the center of the scene is (0,0,0)
    # for the cartesian coordinates, but it's better to have the viewpoint and
    # object rotation about the center of the lattice. Therefore, we grab the
    # center of the lattice, and use this location to translate all objects in
    # the scene such that this is the new center.
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    lattice_center = bpy.data.objects["Cube"].location.copy()
    for obj in bpy.data.objects:
        obj.location = numpy.subtract(obj.location, lattice_center)

    # -------------------------------------------------------------------------

    # CONFIGURING THE REST OF THE SCENE

    # Camera
    cam_data = bpy.data.cameras.new(name="MyCam")
    cam_ob = bpy.data.objects.new(name="MyCam", object_data=cam_data)
    scene.collection.objects.link(cam_ob)  # instance the camera object in the scene
    scene.camera = cam_ob  # set the active camera
    cam_ob.rotation_euler = numpy.radians((70, 0, 93))
    cam_ob.location = (30, 2, 11)
    # cam_ob.data.type = 'ORTHO' # 'PERSP'

    # Sun
    light_data = bpy.data.lights.new("MyLight", "SUN")
    light_ob = bpy.data.objects.new(name="MyLight", object_data=light_data)
    scene.collection.objects.link(light_ob)

    # Set sun to move along with the camera. This is because we don't want
    # shadows changing in the viewport for crystal structures.
    light_ob.parent = cam_ob
    light_ob.location = (4, 50, 4)
    light_ob.rotation_euler = numpy.radians((60, 10, 150))

    # Background (aka the blender "World")
    world = bpy.data.worlds.new(name="MyWorld")
    world.color = (1, 1, 1)
    scene.world = world

    # -------------------------------------------------------------------------

    ## Center all objects at the origin  # fails as-is. consider centering camera to lattice
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

    ## scale the whole crystal structure
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.transform.resize(value=(1.29349, 1.29349, 1.29349))

    # update view to include all the changes we made above
    bpy.context.view_layer.update()

    # set verge3D settings
    # bpy.context.scene.v3d_export.use_shadows = False
    # bpy.context.scene.v3d_export.lzma_enabled = (
    #     True  # add compressed files (fails for some reason)
    # )
    # bpy.context.scene.v3d_export.aa_method = "MSAA8"
    # bpy.data.objects["MyCam"].data.v3d.orbit_min_distance = 15
    # bpy.data.objects["MyCam"].data.v3d.orbit_max_distance = 100
    #
    # export for Verge3D
    # bpy.ops.export_scene.v3d_gltf(filepath=save_path)

    # The format we save the file as depends on the ending of the filename
    if filename.endswith(".blend"):
        # save this to a blender file
        bpy.ops.wm.save_as_mainfile(filepath=filename)
    elif filename.endswith(".glb"):
        # export in the gltf 2.0 format (.glb file)
        bpy.ops.export_scene.gltf(filepath=filename)
    else:
        raise Exception("unknown format used")


def main():

    # get the arguments passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments.
    arguments = sys.argv[sys.argv.index("--") + 1 :]

    # To pull out the arguments passed to the script, we need to tell the parser
    # what they will be in advance.
    parser = argparse.ArgumentParser()
    parser.add_argument("--lattice", dest="lattice")
    parser.add_argument("--sites", dest="sites")
    parser.add_argument("--save", dest="filename")

    # we can now pull out the arguments passed into the command
    parsed_arguments = parser.parse_args(arguments)

    # Run the function we defined above
    make_structure_blend(
        parsed_arguments.lattice,
        parsed_arguments.sites,
        parsed_arguments.filename,
    )


# This is boiler plate code that calls the main function when this script is
# ran with python directly.
if __name__ == "__main__":
    main()
