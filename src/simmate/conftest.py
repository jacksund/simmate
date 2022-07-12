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


import os
import shutil

import pytest
from click.testing import CliRunner
from django.contrib.auth.models import User
from prefect.testing.utilities import prefect_test_harness

from simmate.utilities import get_directory
from simmate.toolkit import Structure, Composition, base_data_types
from simmate.database.base_data_types import Spacegroup
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
    # We want the full path of these filenames, so we that's why there are
    # extra os joins here.
    structure_dir = os.path.join(
        os.path.dirname(base_data_types.__file__),
        "test",
        "test_structures",
    )
    cif_filenames = [os.path.join(structure_dir, f) for f in os.listdir(structure_dir)]
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
        filename.split(os.path.sep)[-1].strip(".cif"): Structure.from_file(filename)
        for filename in STRUCTURE_FILES
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


def copy_test_files(
    tmpdir,
    test_directory: str,
    test_folder: str,
):
    """
    This is a test utility that takes a given directory and copies it's content
    over to a temporary directory. You'll often use this when you want to modify
    files within the test directory (which is often the case with ErrorHandlers).

    Here is an example use-case:
    ``` python
    from somewhere import ExampleHandler
    from simmate.conftest import copy_test_files

    def test_example(tmpdir):

        # Make our temporary directory with copied files
        copy_test_files(
            tmpdir,
            test_directory=__file__,
            test_folder="test_example",
        )

        # then you can do things like...
        error_handler = ExampleHandler()
        error_handler.check(tmpdir)
    ```
    """

    # grab the path to the directory with all the test files
    source_directory = os.path.join(
        os.path.dirname(os.path.abspath(test_directory)),
        test_folder,
    )

    # recursively copy all files in the directory over to the temporary directory
    shutil.copytree(
        src=source_directory,
        dst=tmpdir,
        dirs_exist_ok=True,
    )


def make_dummy_files(*filenames: str):
    """
    This is a utility that creates files. The content of these files are not
    important -- but they are created because sometimes ErrorHanlders may simply
    check to see that a file exists.
    """

    for filename in filenames:
        # make sure the parent dir of the filename exists
        get_directory(os.path.dirname(filename))

        # now make the file
        with open(filename, "w") as file:
            file.write("This is a dummy file for testing.")


@pytest.fixture(scope="session")
def command_line_runner():
    return CliRunner()


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """
    For all prefect flows and tasks, this will automatically use a dummy-database
    """
    with prefect_test_harness():
        yield
