# -*- coding: utf-8 -*-

import os

import numpy


class DeepmdSet:
    """
    This class works simply as a converter. You provide it a list of 
    IonicStepStructures that have forces and energies, and it will create a
    deepmd input for you.
    
    The "set" input is really a folder made of 4 files. An example folder looks 
    like this:
      set.000
          box.npy
          coord.npy
          energy.npy
          force.npy
    
    These .npy are "numpy" files, where the data included in each is...
      box = lattice matrixes
      coord = site's cartesian coordinates
      energy = calculated energies
      force = calculated forces for sites
    
    All data is collapsed to 1D arrays. For example, this means the 3x3 lattice matrix
    becomes a 1x9 list of numbers and the entire file is a list of matricies. The
    same is done to forces, coords, and energies.
    
    All data here is available from an IonicStepStructure in our database, so
    this is our current input format.
    """

    # TODO: currently we use the IonicStepStructure from our relaxation database
    # but in the future this should be a core class that extends the pymatgen
    # Structure object. So for the moment, the ionic_step_structures can be
    # provide like so:
    #
    # from simmate.configuration.django import setup_full  # sets database connection
    # from simmate.database.local_calculations.relaxation.mit import MITRelaxationStructure
    # ionic_step_structures = MITRelaxationStructure.objects.filter(
    #     energy__isnull=False, site_forces__isnull=False
    # ).all()
    #
    # from simmate.calculators.deepmd.inputs.set import DeepmdSet
    # DeepmdSet.to_folder(ionic_step_structures)
    #

    @staticmethod
    def to_folder(ionic_step_structures, foldername="set.000"):

        # because we are using the database model, we first want to convert to
        # pymatgen structures objects
        structures = [structure.to_pymatgen() for structure in ionic_step_structures]

        # DeePMD only allows one composition in each set, where all element types
        # are in the same order. To ensure this, we check that the compositons are
        # all equal. NOTE: we assume the structures have been sanitized bc we
        # are pulling from our database.
        first_composition = structures[0].composition
        for structure in structures:
            if structure.composition != first_composition:
                raise Exception(
                    "DeePMD requires that each structure in a set be the same composition!"
                    " This includes each structure having the same number of sites."
                )

        # We iterate through each structure (and its data) to compile everything
        # into the deepmd list format.
        lattices = []
        coordinates = []
        forces = []
        energies = []
        for structure, structure_data in zip(structures, ionic_step_structures):

            # flatten the lattice matrix to a 1D array and add to our list
            lattice_flat = structure.lattice.matrix.flatten()
            lattices.append(lattice_flat)

            # flatten the cartesian coordinates to a 1D array and add to our list
            coords_flat = structure.cart_coords.flatten()
            coordinates.append(coords_flat)

            # flatten the forces to a 1D array and add to our list
            forces_flat = numpy.array(structure_data.site_forces).flatten()
            forces.append(forces_flat)

            # the energy is just single value so we can add it to our list
            energies.append(structure_data.energy)

        # Now we want to convert all lists to numpy. Note, the dtype used here
        # is to clear a warning that prints when we have arrays of different
        # lengths. This happens when we have structures with different nsites.
        lattices = numpy.array(lattices)
        coordinates = numpy.array(coordinates, dtype=object)
        forces = numpy.array(forces, dtype=object)
        energies = numpy.array(energies)

        # now write our numpy files to the folder specified
        for filename, filedata in [
            ("box.npy", lattices),
            ("coord.npy", coordinates),
            ("energy.npy", energies),
            ("force.npy", forces),
        ]:
            with open(os.path.join(foldername, filename), "wb") as file:
                numpy.lib.format.write_array(
                    fp=file, array=filedata,
                )
