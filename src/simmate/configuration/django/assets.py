# -*- coding: utf-8 -*-

import os
import zipfile

from simmate import website


def unpack_assets():
    """
    For our website interface, we need a lot of extra files -- such as the
    javascript, css, and scss files for Material Kit, jQuery, and more. We don't
    want these files taking up a ton of space in our repo, but we do want them
    included! Therefore we store them as a compressed zip file inside...
      simmate.website.static_files ---> material_kit_assests.zip
    This function is to unpack these assests when they are first needed.
    Users should never have to call this function. Instead, it is called when
    the "simmate run-server" command is issued.
    """

    # OPTIMIZE: could I instead make this a CDN in the future?

    # First we grab the location of the zip file
    django_directory = os.path.dirname(os.path.abspath(website.__file__))
    static_foldername = os.path.join(django_directory, "static_files")
    zip_filename = os.path.join(static_foldername, "material_kit_assets.zip")
    unpacked_foldername = os.path.join(static_foldername, "assets")

    # check if the assets have been unzip already. If they were, we can just
    # exit this function without needing to do anything else. Otherwise, we
    # need to unzip the files.
    if not os.path.exists(unpacked_foldername):
        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall(static_foldername)
