# -*- coding: utf-8 -*-

"""
This file hosts common functions that are used throughout Simmate
"""

import os
from tempfile import TemporaryDirectory


def get_directory(dir):

    # There are many cases where the user can choose their working directory
    # for a given calculation, where they can pass a number of options in.
    # This includes... None, a string, or a TemporaryDirectory instance.
    # I consistently want to handle these inputs and thus make this utility.
    # Based on the input, I do the following:
    #   None --> I return the pull path to python's current working directory
    #   TemporaryDirectory --> I return the full path to this directory
    #   str --> I make the directory if it doesnt exist and then return the path

    # Avoid overusing this! It should often only exist at the highest level
    # for a Task! This means you'll want it in the Task.run() method and
    # nowhere else.

    # if no directory was provided, use the current working directory
    if not dir:
        dir = os.getcwd()
    # if the user provided a tempdir, we want it's name
    elif isinstance(dir, TemporaryDirectory):
        dir = dir.name
    # otherwise make sure the directory the user provided exists and if it does
    # not, then make it!
    else:
        # !!! Or should I assert the directory exists and raise an error if not?
        if not os.path.exists(dir):
            os.mkdir(dir)
    # and return the full path to the directory
    return dir
