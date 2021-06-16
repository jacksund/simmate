# -*- coding: utf-8 -*-

"""
This file hosts common functions that are used throughout Simmate
"""

import os
import itertools
from tempfile import TemporaryDirectory


def get_directory(dir):

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
        for combo in itertools.combinations(system_cleaned, i+1):
            # Combo will be a tuple of elements that we then convert back to a 
            # chemical system. We also sort this alphabetically.
            #   ex: ("Y", "C", "F") ---> "C-F-Y"
            subsystem = "-".join(sorted(combo))
            subsystems.append(subsystem)
    
    return subsystems
