# -*- coding: utf-8 -*-

import os
import tempfile
import time

from django.shortcuts import render

from simmate.toolkit import Structure
from simmate.database.base_data_types import Spacegroup
from simmate.visualization.structure import make_blender_structure
from simmate.configuration.django import settings
from simmate.utilities import get_directory
from simmate.website.core_components.utilities import render_from_table


def symmetry(request):
    return render_from_table(
        request=request,
        template="core_components/symmetry.html",
        context={"active_tab_id": "extras"},
        table=Spacegroup,
        view_type="list",
        primary_key_field="number",
    )


def spacegroup(
    request,
    spacegroup_number: str,
):
    return render_from_table(
        request=request,
        request_kwargs={"spacegroup_number": spacegroup_number},
        template="core_components/spacegroup.html",
        context={"active_tab_id": "extras"},
        table=Spacegroup,
        view_type="retrieve",
        primary_key_field="number",
        primary_key_url="spacegroup_number",
    )


def structure_viewer(request):

    # Grabs all data after the '?' in the URL
    query = request.GET.dict()

    # convert the query to a Structure object
    structure_string = query.get("structure_string", "")
    structure = Structure.from_database_string(structure_string)

    # We want to make a 3d structure file. We make this so it...
    #   1. has a random name that ends with ".glb"
    #   2. is a temporary file (deletes once finished)
    #   3. is located in the static root folder
    # Note we make this file in the static directory because we want to use
    # "load_static" to grab it in the template
    temp_dir = get_directory(
        settings.STATIC_ROOT
    )  # use get_dir to ensure folder exists
    temp_file = tempfile.NamedTemporaryFile(
        dir=temp_dir,
        suffix=".glb",
        # BUG (the fix is below): if delete=True, this sets up a race condition
        # of when the user recieves the file versus when it is deleted.
        delete=False,
    )
    temp_filname_base = os.path.basename(temp_file.name)

    # BUG FIX: Because we can make these temporary files automatically delete,
    # we need to prevent 3D files from building up over time and taking up
    # room on the server/disk. We therefore automatically delete any files that
    # are older than N seconds. This process can be slow, but it adds minimal
    # overhead to the blender-creation process.
    detete_old_3d_files()

    # Use blender to create a temporary glb file. Note, the output here
    # may be useful for debugging, but it isn't used at the moment.
    output = make_blender_structure(structure, filename=temp_file.name)

    # we pass the base name to the template so that it knows where the static
    # file is located (template assumes static directory)
    context = {"3d_structure_filename": temp_filname_base}
    template = "core_components/structure_viewer.html"
    return render(request, template, context)


def test_viewer(request):

    # TODO: switch to a test structure that is present in the source code
    # from simmate.conftest import STRUCTURE_FILES
    structure = Structure.from_file(
        "/home/jacksund/Documents/spyder_wd/test_structures/SrSiN2_mp-4549_primitive.cif"
    )

    context = {"structure": structure}
    template = "core_components/test.html"
    return render(request, template, context)


def detete_old_3d_files(time_cutoff: float = 60):
    """
    Goes through the static directory and finds all "tmp***.glb" files that
    are older than a given time cutoff. Each of these files is then deleted.

    Parameters
    ----------
    - `time_cutoff`:
        The time (in seconds) required to determine whether a file is old or not.
        The default is 60 seconds.
    """
    # load the full path to the desired directory
    directory = os.path.join(settings.DJANGO_DIRECTORY, "static")

    # grab all files/folders in this directory and then limit this list to those
    # that are...
    #   1. NOT folders
    #   2. start with "tmp"
    #   3. end with ".glb"
    #   3. haven't been modified for at least time_cutoff
    filenames = []
    for filename in os.listdir(directory):
        filename_full = os.path.join(directory, filename)
        if (
            not os.path.isdir(filename_full)
            and filename.startswith("tmp")
            and filename.endswith(".glb")
            and time.time() - os.path.getmtime(filename_full) > time_cutoff
        ):
            filenames.append(filename_full)

    # now go through this list and delete the files that met the criteria.
    # If the file fails to be deleted, we just ingore it and move on
    for filename in filenames:
        try:
            os.remove(filename)
        except:
            continue
