# -*- coding: utf-8 -*-

"""
This file hosts common functions that are used throughout Simmate
"""

import os
import itertools
from tempfile import TemporaryDirectory
import shutil


def get_directory(directory=None):

    # There are many cases where the user can choose their working directory
    # for a given calculation, where they can pass a number of options in.
    # This includes... None, a string, or a TemporaryDirectory instance.
    # I consistently want to handle these inputs and thus make this utility.
    # Based on the input, I do the following:
    #   None --> I return the full path to python's current working directory
    #   TemporaryDirectory --> I return the full path to the given temp directory
    #   str --> I make the directory if it doesnt exist and then return the path

    # Avoid overusing this! It should often only exist at the highest level
    # for a Task! This means you'll want it in the Task.run() method and
    # nowhere else.

    # if no directory was provided, use the current working directory
    if not directory:
        directory = os.getcwd()
    # if the user provided a tempdir, we want it's name
    elif isinstance(directory, TemporaryDirectory):
        directory = directory.name
    # otherwise make sure the directory the user provided exists and if it does
    # not, then make it!
    else:
        # We use mkdirs instead of mkdir because we want to make these directory
        # recursively. That is, we can do "path/to/newfolder1/newfolder2" where
        # multiple folders can be made with one call.
        # Also if the folder already exists, we don't want to raise an error.
        os.makedirs(directory, exist_ok=True)
    # and return the full path to the directory
    return directory


def empty_directory(directory, files_to_keep=[]):

    # grab all of the files and folders inside the listed directory
    for filename in os.listdir(directory):
        if filename not in files_to_keep:
            # check if we have a folder or a file.
            # Folders we delete with shutil and files with the os module
            if os.path.isdir(filename):
                shutil.rmtree(filename)  # ignore_errors=False
            else:
                os.remove(filename)


def get_chemical_subsystems(chemical_system):

    # TODO: this will may be better located elsewhere. Maybe even as a method for
    # the Composition class.

    # Given a chemical system, this returns all chemical systems that are also
    # contained within it. For example, "Y-C" would return ["Y", "C", "C-Y"].
    # Note that the returned list has elements of a given system in alphabetical
    # order (i.e. it gives "C-Y" and not "Y-C")

    # Convert the system to a list of elements
    system_cleaned = chemical_system.split("-")

    # Now generate all unique combinations of these elements. Because we also
    # want combinations of different sizes (nelements = 1, 2, ... N), then we
    # put this in a for-loop.
    subsystems = []
    for i in range(len(system_cleaned)):
        # i is the size of combination we want. We now ask for each unique combo
        # of elements at this given size.
        for combo in itertools.combinations(system_cleaned, i + 1):
            # Combo will be a tuple of elements that we then convert back to a
            # chemical system. We also sort this alphabetically.
            #   ex: ("Y", "C", "F") ---> "C-F-Y"
            subsystem = "-".join(sorted(combo))
            subsystems.append(subsystem)

    return subsystems


def get_sanitized_structure(structure):
    """
    Run symmetry analysis and "sanitization" on the pymatgen structure
    """

    # TODO Move this to a Simmate.Structure method in the future

    # Make sure we have the primitive unitcell first
    # We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
    # built-in Structure.get_primitive_structure function:
    #   structure = structure.get_primitive_structure(0.1) # Default tol is 0.25

    # Default tol is 0.01, but we use a looser 0.1 Angstroms
    # from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    # structure_primitive = SpacegroupAnalyzer(structure, 0.1).find_primitive()
    # BUG: with some COD structures, this symm analysis doesn't work. I need
    # to look into this more and figure out why.

    # Default tol is 0.25 Angstroms
    structure_primitive = structure.get_primitive_structure()

    # Convert the structure to a "sanitized" version.
    # This includes...
    #   (i) an LLL reduction
    #   (ii) transforming all coords to within the unitcell
    #   (iii) sorting elements by electronegativity
    structure_sanitized = structure_primitive.copy(sanitize=True)

    # return back the sanitized structure
    return structure_sanitized
