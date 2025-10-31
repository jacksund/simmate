# -*- coding: utf-8 -*-

from pathlib import Path

import numpy
import pandas
from django_pandas.io import read_frame
from sklearn.model_selection import train_test_split

from simmate.toolkit import Composition, Structure
from simmate.utilities import get_directory


class DeepmdDataset:
    """
    This class works simply as a converter. You provide it a list of
    database entries that have forces and energies, and it will create a
    deepmd input for you.

    There are two types of input formats for DeepMD: System and Mixed Type.
    System is appropriate for models with a limited number of elements and
    each provided structure should have the same set of elements. Mixed Type
    is appropriate for larger models (DPA-1 and DPA-2) and the structures can
    have any number of elements.

    1) System:
    The input consists of 2 "type" files and then a subfolder made of 4 files for
    the actaul data. An example folder looks like this:
        type.raw
        type_map.raw
        set.000
            box.npy
            coord.npy
            energy.npy
            force.npy

    The "type" files are very simple. "type_map.raw" is just a list of elements
    and the "type.raw" is our composition listing what each site is. For example,
    H20 (water) would just be...
        type_map.raw --> H O
        type.raw --> 0 0 1

    These .npy are "numpy" files, where the data included in each is...
      box = lattice matrixes
      coord = site's cartesian coordinates
      energy = calculated energies
      force = calculated forces for sites

    All data is collapsed to 1D arrays. For example, this means the 3x3 lattice matrix
    becomes a 1x9 list of numbers and the entire file is a list of matricies in this
    format. The same is done to forces, coords, and energies.

    Note this is the folder/file format for EACH composition. So this class creates
    many of these folders if you provide input structures that have varying
    compositions (such as CoO2, Co2O4, Co3O6, etc.).

    Further, we split the input structures into training and test datasets. So
    the final folder setup will look like...
    deepmd_data
        CoO2_train
        CoO2_test
        Co2O4_train
        Co2O4_test
        << etc. >>

    2) Mixed Type
    This input is similar to the System format, but is designed for when there
    are many different compositions with varying elements. In these situations,
    there may be sparse data for some compositions. Instead, compositions are
    organized by number of atoms, then each number of elements has it's own subfolder.
    The head of the folder will look like this:

    train
        [num_atom]
            sys.xxxx
    valid
        [num_atom]
            sys.xxxx

    With each sys.xxxx having he same format as the System format with some
    differences.

    The type_map.raw for each sys.xxxx folder will be the same and includes all of
    the elements in the training data. The type.raw file that is normally used,
    implies that the structures have the same atom indices for all frames in the
    sys.xxxx. In this format, this file is filled with 0s and we instead include
    an additional real_atom_types.npy file in each set.xxxx folder.
    This is an array of shape Nframes*Natoms with integers describing atom types
    in each frame.


    All data required is available from Relaxation or StaticEnergy tables in our
    database, so this is our current input format.
    """

    # TODO: currently we use the IonicStepStructure from our relaxation database
    # but in the future this should be a core class that extends the pymatgen
    # Structure object. So for the moment, the ionic_step_structures can be
    # provide like so:
    #
    # from simmate.database import connect
    # from simmate.database.workflow_results import MITRelaxationStructure
    # ionic_step_structures = MITRelaxationStructure.objects.filter(
    #     energy__isnull=False, site_forces__isnull=False
    # ).all()
    #
    # from simmate.apps.deepmd.inputs.set import DeepmdSet
    # DeepmdSet.to_folder(ionic_step_structures)
    #
    def __init__(
        self,
        structure_entries,
    ):
        self.structure_entries = structure_entries

    def get_train_valid_dataframes(
        self,
        test_size: float = 0.2,
    ):
        ionic_step_structures = self.structure_entries

        # convert the ionic_step_structures queryset to a pandas dataframe
        structures_dataframe = read_frame(ionic_step_structures)

        # because we are using the database model, we first want to convert to
        # pymatgen structures objects and add a column to the dataframe for these
        #
        #   structures_dataframe["structure"] = [
        #       structure.to_toolkit() for structure in ionic_step_structures
        #   ]
        #
        # BUG: the read_frame query creates a new query, so it may be a different
        # length from ionic_step_structures. For this reason, we can't iterate
        # through the queryset like in the commented out code above. Instead,
        # we need to iterate through the dataframe rows.
        # See https://github.com/chrisdev/django-pandas/issues/138 for issue
        structures_dataframe["structure"] = [
            Structure.from_str(s.structure, fmt="POSCAR")
            for _, s in structures_dataframe.iterrows()
        ]

        # split the structures into test and training sets randomly
        dataframe_train, dataframe_valid = train_test_split(
            structures_dataframe,
            test_size=test_size,
        )
        return dataframe_train, dataframe_valid

    def to_system(
        self,
        directory: Path | str = "deepmd_data",
        test_size: float = 0.2,
    ):
        # Grab the path to the desired directory and create it if it doesn't exist
        directory = get_directory(directory)

        # Create training and validation dataframes
        dataframe_train, dataframe_valid = self.get_train_valid_dataframes(test_size)

        # The System format is assumed to have the same set of elements with the same
        # type mapping in every system folder. We find the type_map based on
        # the first structure in the data
        type_map = [
            str(i) + "\n" for i in dataframe_train["chemical_system"][0].split("-")
        ]
        # The process for creating files is the same for both the test and training
        # sets, where the only difference is the folder ending we add to each. Other
        # methods (such as creating the input.json for DeePMD) require the names
        # of the folders created here -- so we also store them in lists to return
        # at the end of the function too.
        folders_train = []
        folders_valid = []
        for folder_suffix, dataframe_set, folder_list in [
            ("train", dataframe_train, folders_train),
            ("valid", dataframe_valid, folders_valid),
        ]:
            # grab a list of the unique compositions in our set of structures
            unique_compositions = dataframe_set.formula_full.unique()

            # for each composition, we want to filter off those structures and
            # then write them to a individual folder for deepmd.
            # note these compositions are just strings right now.
            for composition_str in unique_compositions:
                # convert to a pymatgen composition object
                composition = Composition(composition_str)

                # Let's establish where this folder will be and also store it
                composition_directory = directory / f"{composition_str}_{folder_suffix}"
                folder_list.append(composition_directory)
                # this creates the directory or grabs the full path
                composition_directory = get_directory(composition_directory)

                # first let's write the type_map file, which is just a list of elements
                mapping_filename = composition_directory / "type_map.raw"
                with mapping_filename.open("w") as file:
                    for element in composition:
                        file.write(str(element) + "\n")

                # Now we can write the type file while also establish the mapping.
                # Note the mapping is just the index (0, 1, 2, ...) of each element.
                type_filename = (
                    directory / f"{composition_str}_{folder_suffix}" / "type.raw"
                )
                with type_filename.open("w") as file:
                    for mapping_value, element in enumerate(composition):
                        for i in range(int(composition[element])):
                            file.write(str(mapping_value) + "\n")

                # Now we need the relevent structures. Let's filter off the
                # structures that have this composition for us to use below
                dataframe_subset = dataframe_set[
                    dataframe_set["formula_full"] == composition_str
                ]

                # We iterate through each structure (and its data) to compile everything
                # into the deepmd list format.
                lattices = []
                coordinates = []
                forces = []
                energies = []
                # Note the "_," here is because row index is returned but we dont need it
                for _, structure_data in dataframe_subset.iterrows():
                    # grab the pymatgen structure
                    structure = structure_data.structure

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

                # Now we want to convert all lists to numpy.
                lattices = numpy.array(lattices)
                coordinates = numpy.array(coordinates)
                forces = numpy.array(forces)
                energies = numpy.array(energies)
                # Note, the dtype=object can be added as a kwarg here in order to clear
                # a warning that prints when we have arrays of different lengths. This
                # happens when we have structures with different nsites. However, this
                # causes errors with DeepMD which can load object type arrays.

                # for now we assume the dataset is written to set.000, so we
                # make that folder first.
                set_directory = composition_directory / "set.000"
                set_directory = get_directory(set_directory)
                # now write our numpy files to the folder specified
                for filename, filedata in [
                    ("box.npy", lattices),
                    ("coord.npy", coordinates),
                    ("energy.npy", energies),
                    ("force.npy", forces),
                ]:
                    filename_full = set_directory / filename
                    with filename_full.open("wb") as file:
                        numpy.lib.format.write_array(fp=file, array=filedata)

        # all of the folders have been created and we return a list of where
        return folders_train, folders_valid, type_map

    def to_mixed_type(
        self,
        directory: Path | str = "deepmd_data",
        test_size: float = 0.2,
    ):
        # Grab the path to the desired directory and create it if it doesn't exist
        directory = get_directory(directory)

        # Create training and validation dataframes
        dataframe_train, dataframe_valid = self.get_train_valid_dataframes(test_size)

        type_map = []
        # We need the type map for the elements in our data. To do this,
        # we need to create a list of all unique elements in the structures.
        for df in [dataframe_train, dataframe_valid]:
            unique_systems = df["chemical_system"].unique()
            for system in unique_systems:
                system = system.split("-")
                type_map.extend(system)
        # We convert our element map to a pandas Series, remove any duplicates,
        # and sort alphabetically
        type_map = pandas.Series(type_map)
        type_map = type_map.drop_duplicates().sort_values().reset_index(drop=True)

        # The process for creating files is the same for both the test and training
        # sets, where the only difference is which folder we add to. Other
        # methods (such as creating the input.json for DeePMD) require the names
        # of the folders created here -- so we also store them in lists to return
        # at the end of the function too.
        folders_train = []
        folders_valid = []
        for folder_suffix, dataframe_set, folder_list in [
            ("train", dataframe_train, folders_train),
            ("valid", dataframe_valid, folders_valid),
        ]:
            # For each number of atoms in the structures, we want to create a
            # new folder with a sys.xxx folder containing all of the structures
            unique_lengths = dataframe_set["nsites"].unique()
            # for each unique number of atoms, we want to filter our database
            # for corresponding structures, get box, coord, energy, force, and atom
            # types for each structure, and write the full list as .npy binary files
            for length in unique_lengths:
                # Let's establish where this folder will be and also store it
                length_directory = directory / f"{folder_suffix}/{length}/sys.000000"
                folder_list.append(length_directory)
                # this creates the directory or grabs the full path
                length_directory = get_directory(length_directory)

                # Now let's write the type_map file, which is just a list of elements
                mapping_filename = length_directory / "type_map.raw"
                with mapping_filename.open("w") as file:
                    for element in type_map:
                        file.write(str(element) + "\n")

                # Now we can write the type file which is just a set of 0s for
                # this format.
                type_filename = length_directory / "type.raw"
                with type_filename.open("w") as file:
                    for i in range(length):
                        file.write("0" + "\n")

                # Now lets filter the dataframe for all structures of this length
                dataframe_subset = dataframe_set.loc[dataframe_set["nsites"] == length]

                # We iterate through each structure (and its data) to compile everything
                # into the deepmd list format.
                lattices = []
                coordinates = []
                forces = []
                energies = []
                atom_types = []
                # Note the "_," here is because row index is returned but we dont need it
                for _, structure_data in dataframe_subset.iterrows():
                    # grab the pymatgen structure
                    structure = structure_data.structure

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

                    # the atom types are converted to the element map indices
                    atom_types.append(
                        [
                            type_map[type_map == i.name].index[0]
                            for i in structure.species
                        ]
                    )

                # Now we want to convert all lists to numpy.
                lattices = numpy.array(lattices)
                coordinates = numpy.array(coordinates)
                forces = numpy.array(forces)
                energies = numpy.array(energies)
                atom_types = numpy.array(atom_types)

                # for now we assume the dataset is written to set.000, so we
                # make that folder first.
                set_directory = length_directory / "set.000"
                set_directory = get_directory(set_directory)
                # now write our numpy files to the folder specified
                for filename, filedata in [
                    ("box.npy", lattices),
                    ("coord.npy", coordinates),
                    ("energy.npy", energies),
                    ("force.npy", forces),
                    ("real_atom_types.npy", atom_types),
                ]:
                    filename_full = set_directory / filename
                    with filename_full.open("wb") as file:
                        numpy.lib.format.write_array(fp=file, array=filedata)

        # all of the folders have been created and we return a list of where
        return folders_train, folders_valid, type_map
