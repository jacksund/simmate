# -*- coding: utf-8 -*-

"""
This file hosts common functions that are used throughout Simmate
"""

import os
import itertools
from tempfile import TemporaryDirectory, mkdtemp
import shutil
import warnings

import numpy


def get_doc_from_readme(file):
    
    # We assume the file is in the same directory and named "README.rst"
    file_directory = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(file_directory, "README.rst"),
        encoding="utf-8",
    ) as doc_file:
        doc = doc_file.read()
    
    return doc


def get_directory(directory=None):

    # There are many cases where the user can choose their working directory
    # for a given calculation, where they can pass a number of options in.
    # This includes... None, a string, or a TemporaryDirectory instance.
    # I consistently want to handle these inputs and thus make this utility.
    # Based on the input, I do the following:
    #   None --> I return the full path to a new folder inside python's
    #            current working directory
    #   TemporaryDirectory --> I return the full path to the given temp directory
    #   str --> I make the directory if it doesnt exist and then return the path

    # Avoid overusing this! It should often only exist at the highest level
    # for a Task! This means you'll want it in the Task.run() method and
    # nowhere else.

    # if no directory was provided, we create a new folder within the current
    # working directory. All of these folders are named randomly.
    # BUG: we can't name these nicely (like simmate-task-001) because that will
    # introduce race conditions when making these folders in production.
    # !!! What if I name this folder off of the workflow run id in the future?
    if not directory:

        # create a directory in the current working directory. Note, even though
        # we are creating a "TemporaryDirectory" here, this directory is never
        # actually deleted.
        directory = mkdtemp(prefix="simmate-task-", dir=os.getcwd())

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


def estimate_radii(composition, radius_method="ionic"):

    # grab the elements as a list of Element objects
    elements = composition.elements

    # change the list of elements to radii list (atomic/vdw/metallic/ionic)
    if radius_method == "atomic":
        radii = [element.atomic_radius for element in elements]
    elif radius_method == "atomic_calculated":
        radii = [element.atomic_radius_calculated for element in elements]
    elif radius_method == "van_der_waals":
        radii = [element.van_der_waals_radius for element in elements]
    elif radius_method == "metallic":
        radii = [element.metallic_radius for element in elements]
    elif radius_method == "ionic":
        # In order to predict the radius here, we first need to predict the
        # oxidation states. Note that this prediction changes composition to
        # be made of Specie objects instead of Element objects.
        # By converting to the reduced_composition first, we see a massive speed
        # up -- this is done with max_sites=-1
        composition = composition.add_charges_from_oxi_state_guesses(max_sites=-1)
        elements = composition.elements
        # Now we can grab the predicted radii
        # If the estimated oxidation state is zero OR if the predicted oxidation
        # state does not have an available radius (e.g H+ doesn't have a reported
        # radius in our dataset), I grab the atomic radius.
        # BUG: This will print a lot of warnings when the ionic radius doesn't exist.
        # I expect these warnings, so I choose to suppress them here.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # dont print the warnings!
            radii = []
            for element in elements:
                # attempt to grab the radius
                radius = element.ionic_radius
                # if the radius is None, then we have an error and should grab
                # the atomic radius instead
                if not radius:
                    # note the .element is because we have our element
                    # variable as a Specie object right now.
                    radius = element.element.atomic_radius
                radii.append(radius)

    # Some methods above might not give a radius for elements. For example,
    # N will not provide a Metallic radius. In cases like this, we should let
    # the user know.
    if None in radii:
        raise Exception(
            f"{radius_method} radius_method is not allowed for one or more"
            " of the elements in composition"
        )

    # this returns a list of radii, where the order is assumed the same as the
    # order of elements in composition
    return radii


def estimate_volume(composition, radius_method="ionic", packing_factor=1.35):

    # 1.35 is 74% packing efficieny (hexagonal packing) so we select this for
    # the default packing_factor

    # grab a list of radii (assumed to be in order of elements in composition)
    radii = estimate_radii(composition, radius_method)

    # take the radii and find the corresponding spherical volume for each atom type
    volumes = [4 / 3 * numpy.pi * (radius ** 3) for radius in radii]

    # find the total volume of all spheres in the composition
    total_volume = sum(
        [
            composition[element] * volume
            for element, volume in zip(composition.elements, volumes)
        ]
    )
    # based on the packing of these spheres, we want to scale the volume of the
    # lattice better packing corresponds to a lower packing_factor
    total_volume *= packing_factor

    return total_volume


def distance_matrix(composition, radius_method="ionic", packing_factor=0.5):

    # grab a list of radii (assumed to be in order of elements in composition)
    radii = estimate_radii(composition, radius_method)

    # multiply the radii by some factor that you want limit the overlap by
    # for example, if we don't want sites any closer than 50% their radii so
    # we can set factor=0.5.
    # Note, float() strips the unit (ang) from the value to avoid errors.
    radii = [float(radius * packing_factor) for radius in radii]

    # Create the element distance matrix
    # There doesn't seem to be an easy way to get iterools.product() to a matrix
    # so I iterate through the possible combinations manually.
    # OPTIMIZE: note this is really a symmetrical matrix so I'm actually caclulating
    # things twice.
    matrix = []
    for radius1 in radii:
        row = []
        for radius2 in radii:
            limit = radius1 + radius2
            row.append(limit)
        matrix.append(row)

    # convert the result matrix of list matrix to a numpy array before returning
    element_distance_matrix = numpy.array(matrix)
    return element_distance_matrix
