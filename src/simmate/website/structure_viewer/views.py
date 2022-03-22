# -*- coding: utf-8 -*-

import os
import tempfile

from django.shortcuts import render

from simmate.toolkit import Structure
from simmate.visualization.structure import make_blender_structure
from simmate.configuration.django import settings
from simmate.utilities import get_directory


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
    temp_dir = get_directory(os.path.join(settings.STATIC_ROOT))
    temp_filename = tempfile.NamedTemporaryFile(
        dir=temp_dir,
        suffix=".glb",
        # BUG: if delete=True, I'm not sure if this sets up a race condition of
        # when the user recieves the file versus when it is deleted.
        delete=False,  
    )
    temp_filname_base = os.path.basename(temp_filename.name)

    # Use blender to create a temporary glb file
    make_blender_structure(structure, filename=temp_filename)

    # we pass the base name to the template so that it knows where the static
    # file is located (template assumes static directory)
    context = {
        "3d_structure_filename": temp_filname_base,
    }
    template = "structure_viewer/main.html"
    return render(request, template, context)


def test_viewer(request):

    structure = Structure.from_file("Documents/SpyderWD/Y2CF2.cif")

    context = {"structure": structure}
    template = "structure_viewer/test.html"
    return render(request, template, context)
