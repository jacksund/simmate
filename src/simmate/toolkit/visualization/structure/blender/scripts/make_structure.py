# -*- coding: utf-8 -*-

import argparse
import json
import sys

import bmesh
import bpy
import numpy

from simmate.toolkit.visualization.coloring import ELEMENT_COLORS_JMOL_RGB

# Blender needs a 4th value for the opacity in addition to the RGB values given
# above. For all materials, we use 255 and append this to all of them here. Blender
# needs these values on a 0-1 scale instead of the 0-255. We address
# this below by dividing all values by 255
COLORING = ELEMENT_COLORS_JMOL_RGB.copy()
for key in COLORING:
    color = COLORING[key]
    color.append(255)
    COLORING[key] = numpy.array(color) / 255


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
        site_color = COLORING[element_symbol]

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
    if filename.suffix == ".blend":
        # save this to a blender file
        bpy.ops.wm.save_as_mainfile(filepath=filename)
    elif filename.suffix == ".glb":
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
