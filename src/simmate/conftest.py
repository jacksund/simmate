# -*- coding: utf-8 -*-

"""
This module is for Simmate's test suite. You'll only use this if you are
contributing to the source code and making new tests.

Nearly all of Simmate's tests stem from toolkit objects, so this file loads sample
objects using the `toolkit.base_data_types` module. These Structures and 
Compositions can be used in any test.

Read more on pytest fixtures [here](https://docs.pytest.org/en/6.2.x/fixture.html).
This file helps share fixtures accross files as described 
[here](https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files).
"""


import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from django.contrib.auth.models import User

from simmate.database.base_data_types import Spacegroup
from simmate.toolkit import Composition, Structure, base_data_types
from simmate.utilities import get_directory
from simmate.website.test_app.models import TestStructure

COMPOSITIONS_STRS = [
    "Fe1",
    "Si2",
    "C4",
    "Ti2O4",
    "Al4O6",
    "Si4N4O2",
    "Si4O8",
    "Sr4Si4N8",
    "Mg4Si4O12",
]


def get_structure_files():
    """
    Lists the full filename paths all of the files in the following directory:
       - toolkit/base_data_types/test/test_structures
    """
    structure_dir = Path(base_data_types.__file__).parent / "test" / "test_structures"
    cif_filenames = [structure_dir / f for f in structure_dir.iterdir()]
    return cif_filenames


STRUCTURE_FILES = get_structure_files()


@pytest.fixture(scope="session", params=COMPOSITIONS_STRS)
def composition(request):
    """
    Gives a iteratible parameter of example compositions, where the compositions
    are given as ToolkitComposition objects.

    Use this fixture when you want to run a test on all of these compositions
    one at a time. For example, you would run a test like...

    ``` python
    # This function will be ran once for each composition
    def test_example(composition):

        # Do something with your composition.
        # We use a dummy example line here.
        assert composition
    ```
    """
    return Composition(request.param)


@pytest.fixture(scope="session")
def sample_compositions():
    """
    Gives a dictionary of example compositions to use, where the compositions
    are given as ToolkitComposition objects.

    Use this fixture when you want to a specific compositions within a test.
    For example, you would run a test like...

    ``` python
    def test_example(sample_compositions):

        # grab your desired composition
        composition = sample_compositions["Si2"]

        # now run any test you'd like with the object.
        # We use a dummy example line here.
        assert composition == Composition("Si2")
    ```
    """
    return {c: Composition(c) for c in COMPOSITIONS_STRS}


@pytest.fixture(scope="session", params=STRUCTURE_FILES)
def structure(request):
    """
    Gives a iteratible parameter of example structures, where the structures
    are given as ToolkitStructure objects.

    Use this fixture when you want to run a test on all of these structures
    one at a time. For example, you would run a test like...

    ``` python
    # This function will be ran once for each structure
    def test_example(structure):

        # Do something with your structure.
        # We use a dummy example line here.
        assert structure
    ```
    """
    return Structure.from_file(request.param)


@pytest.fixture(scope="session")
def sample_structures():
    """
    Gives a dictionary of example structures to use.

    All of these structures are loaded from files located in...
        simmate/toolkit/base_data_types/test/test_structures

    The structures are given as ToolkitStructure objects and the key are the
    filenames they came from (excluding filename extensions)

    Use this fixture when you want to a specific structures within a test.
    For example, you would run a test like...

    ``` python
    def test_example(sample_structures):

        # grab your desired composition
        structure = sample_structures["C_mp-48_primitive"]

        # now run any test you'd like with the object.
        # We use a dummy example line here.
        assert structure
    ```
    """

    # Now load all of the structures. This is a dictionary that where you
    # can access structures with keys like "SiO2_mp-7029_primitive"
    structures = {
        filename.stem: Structure.from_file(filename) for filename in STRUCTURE_FILES
    }

    return structures


@pytest.fixture(scope="session")
def django_db_setup(
    django_db_setup,
    django_db_blocker,
    sample_structures,
    # django_user_model,
):
    """
    This fixture loads test data into the database that can be queried accross
    all other tests. For now, we only add Spacegroups, 10 sample structures,
    and a user.
    """
    with django_db_blocker.unblock():

        # add a user
        User.objects.create_user(
            username="test_user",
            password="test_password",
        )

        # populate spacegroup data
        Spacegroup._load_database_from_toolkit()

        # now add test structures
        for name, structure in sample_structures.items():
            structure_db = TestStructure.from_toolkit(structure=structure)
            structure_db.save()


def copy_test_files(tmp_path, test_directory, test_folder):
    """
    This is a test utility that takes a given directory and copies it's content
    over to a temporary directory. You'll often use this when you want to modify
    files within the test directory (which is often the case with ErrorHandlers).

    If the test_folder given is a compressed file, the zip contents will be
    unpacked and copied to the temporary directory. This is typically done when
    test files are extremely large (e.g. VASP output files)

    Here is an example use-case:
    ``` python
    from somewhere import ExampleHandler
    from simmate.conftest import copy_test_files

    def test_example(tmp_path):

        # Make our temporary directory with copied files
        copy_test_files(
            tmp_path,
            test_directory=__file__,
            test_folder="test_example",  # or "test_example.zip"
        )

        # then you can do things like...
        error_handler = ExampleHandler()
        error_handler.check(tmp_path)
    ```
    """
    # convert to Path objects
    test_directory = Path(test_directory)
    test_folder = Path(test_folder)

    # grab the path to the directory with all the test files
    source_directory = test_directory.absolute().parent / test_folder

    # if the test files are stored in a zip file, uncompress the files to
    # the temporary test directory
    if source_directory.suffix == ".zip":
        shutil.unpack_archive(
            source_directory,
            extract_dir=tmp_path,
        )

    # Otherwise, recursively copy all files in the directory over to
    # the temporary test directory
    else:
        shutil.copytree(
            src=source_directory,
            dst=tmp_path,
            dirs_exist_ok=True,
        )


def make_dummy_files(*filenames: str):
    """
    This is a utility that creates files. The content of these files are not
    important -- but they are created because sometimes ErrorHanlders may simply
    check to see that a file exists.
    """

    for filename in filenames:
        filename = Path(filename)

        # make sure the parent dir of the filename exists
        get_directory(filename.parent)

        # now make the file
        with filename.open("w") as file:
            file.write("This is a dummy file for testing.")


@pytest.fixture(scope="session")
def command_line_runner():
    return CliRunner()


# !!! Disable harness until prefect is reimplemented
# from prefect.testing.utilities import prefect_test_harness
# @pytest.fixture(autouse=True, scope="session")
# def prefect_test_fixture():
#     """
#     For all prefect flows and tasks, this will automatically use a dummy-database
#     """
#     with prefect_test_harness():
#         yield
