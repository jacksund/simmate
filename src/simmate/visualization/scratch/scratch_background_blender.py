# This script is an example of how you can run blender from the command line
# (in background mode with no interface) to automate tasks, in this example it
# creates a text object, camera and light, then renders and/or saves it.
# This example also shows how you can parse command line options to scripts.
#
# Example usage for this test.
#  blender --background --factory-startup --python $HOME/background_job.py -- \
#          --text="Hello World" \
#          --render="/tmp/hello" \
#          --save="/tmp/hello.blend"
#
# Notice:
# '--factory-startup' is used to avoid the user default settings from
#                     interfering with automated scene generation.
#
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.

# cd Anaconda3/envs/jacks_env/Lib/site-packages/jacksund/WarrenLabToolBox/Other
# blender --background --factory-startup --python background_blender.py -- --text="SUP-BLENDER" --save="C:/Users/jacks/Desktop/test.blend" --render="C:/Users/jacks/Desktop/testy"

import bpy

# convert from standards 255x255x255 rgb to blender's 50x50x50 rgb
jmol_coloring = {
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

# to add 4th value for blender
for key in jmol_coloring:
    jmol_coloring[key].append(255)


def example_function(lattice, sites_to_draw, save_path):

    # convert variable from json str to original format
    import json

    lattice = json.loads(lattice)
    sites_to_draw = json.loads(sites_to_draw.replace("'", '"'))

    # Clear existing objects.
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import Verge3D settings
    import addon_utils

    addon_utils.enable(module_name="verge3d")

    scene = bpy.context.scene

    import numpy as np

    # draw sites
    for site in sites_to_draw:
        site_element, site_size, site_loc = site
        site_loc = np.array(site_loc)  # change list to numpy array for functionality
        site_color = (
            np.array(jmol_coloring[site_element]) / 255
        )  # divide each value by 255 to standardize for blender

        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=4, radius=site_size * 0.75, location=site_loc
        )  # creates and sets to active object

        # make material for new object
        materials = bpy.data.materials
        if site_element in materials.keys():
            mat = materials[site_element]
        else:
            mat = bpy.data.materials.new(name=site_element)  # create material
            mat.diffuse_color = site_color
            mat.metallic = 1
            mat.specular_intensity = 0
            mat.roughness = 0.6
        bpy.context.active_object.data.materials.append(
            mat
        )  # append material to selected objects

    # make smooth shading for all then deselect
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action="DESELECT")

    # Add lattice # ISSUE WHERE EACH LINE ISNT PERFECT CIRCLE >>> WILL FIX BY SEPARATING LINES
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=True)
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

    # Split edges, which requires the bmesh module
    # bpy.ops.mesh.edge_split() # doesn't work because of context/poll check
    import bmesh as bmesh

    lattice = bpy.data.objects[0].data  # regular bpy object
    bm = bmesh.new()  # create new bmesh
    bm.from_mesh(lattice)  # fill bmesh with data from bpy object
    bmesh.ops.split_edges(bm, edges=bm.edges)  # spit the edges on the mesh
    bm.to_mesh(lattice)  # write the result data back to the initial bpy object

    bpy.ops.object.convert(target="CURVE")
    bpy.context.object.data.fill_mode = "FULL"
    bpy.context.object.data.bevel_depth = 0.1
    bpy.context.object.data.bevel_resolution = 0
    bpy.context.object.data.bevel_resolution = 3
    bpy.ops.object.shade_smooth()

    # make lattice black
    mat = bpy.data.materials.new(
        name="Lattice"
    )  # create material # can be grabbed later with bpy.data.materials['Test-Material']
    mat.diffuse_color = (0, 0, 0, 1)  # make black
    mat.specular_intensity = 0  # turn of specular
    bpy.context.active_object.data.materials.append(
        mat
    )  # append material to selected objects

    # set lattice origin to geometry (so we can set camera to lattice center)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    lattice_center = bpy.data.objects["Cube"].location.copy()
    # bpy.data.objects['Cube'].location = (0,0,0) #bpy.context.object.location = (0,0,0)
    for obj in bpy.data.objects:
        obj.location = np.subtract(obj.location, lattice_center)

    # Camera
    cam_data = bpy.data.cameras.new("MyCam")
    cam_ob = bpy.data.objects.new(name="MyCam", object_data=cam_data)
    scene.collection.objects.link(cam_ob)  # instance the camera object in the scene
    scene.camera = cam_ob  # set the active camera
    cam_ob.rotation_euler = np.radians((70, 0, 93))
    cam_ob.location = (30, 2, 11)
    # cam_ob.data.type = 'ORTHO' # 'PERSP'

    # Sun
    light_data = bpy.data.lights.new("MyLight", "SUN")
    light_ob = bpy.data.objects.new(name="MyLight", object_data=light_data)
    scene.collection.objects.link(light_ob)
    # set sun to move with camera
    light_ob.parent = cam_ob
    light_ob.location = (4, 50, 4)
    light_ob.rotation_euler = np.radians((60, 10, 150))

    # World
    world = bpy.data.worlds.new("TESTWorld")
    world.color = (1, 1, 1)  # blender 2.79 uses .ambient_color
    scene.world = world

    ## Center all objects at the origin  # fails as-is. consider centering camera to lattice
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

    ## scale the whole crystal structure
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.transform.resize(value=(1.29349, 1.29349, 1.29349))

    # update view to all changes above
    bpy.context.view_layer.update()

    # set verge3D settings
    bpy.context.scene.v3d_export.use_shadows = False
    bpy.context.scene.v3d_export.lzma_enabled = (
        True  # add compressed files (fails for some reason)
    )
    bpy.context.scene.v3d_export.aa_method = "MSAA8"
    bpy.data.objects["MyCam"].data.v3d.orbit_min_distance = 15
    bpy.data.objects["MyCam"].data.v3d.orbit_max_distance = 100

    # save/export files
    if save_path:
        # save the *.blend file
        bpy.ops.wm.save_as_mainfile(filepath=save_path + ".blend")

        # export for Verge3D
        bpy.ops.export_scene.v3d_gltf(filepath=save_path)


def main():
    import sys  # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1 :]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
        "Run blender in background mode with this script:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    # Example utility, add some text and renders or saves it (with options)
    # Possible types are: string, int, long, choice, float and complex.
    parser.add_argument(
        "-l",
        "--lattice",
        dest="lattice",
        type=str,
        required=True,
        help="The lattice matrix to draw (3x3 matrix to json dump)",
    )

    parser.add_argument(
        "-s",
        "--sites",
        dest="sites_to_draw",
        type=str,
        required=True,
        help="List of the sites to draw with each entry in format (element, ionic_radius, cart_coords)",
    )

    parser.add_argument(
        "-S",
        "--save",
        dest="save_path",
        metavar="FILE",
        help="Save the generated file to the specified path",
    )

    args = parser.parse_args(argv)  # In this example we won't use the args

    if not argv:
        parser.print_help()
        return

    if not args.lattice or not args.sites_to_draw:
        print("Error: --lattice and/or sites argument not given, aborting.")
        parser.print_help()
        return

    # Run the example function
    example_function(args.lattice, args.sites_to_draw, args.save_path)

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
