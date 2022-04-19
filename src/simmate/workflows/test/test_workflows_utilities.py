# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.workflows.utilities import (
    get_list_of_all_workflows,
    get_list_of_workflows_by_type,
    get_workflow,
    load_results_from_directories,
    get_unique_parameters,
    parse_parameters,
)


def test_list_of_all_workflows():

    assert get_list_of_all_workflows() == [
        "static-energy/matproj",
        "static-energy/mit",
        "static-energy/neb-endpoint",
        "static-energy/quality04",
        "relaxation/matproj",
        "relaxation/mit",
        "relaxation/neb-endpoint",
        "relaxation/quality00",
        "relaxation/quality01",
        "relaxation/quality02",
        "relaxation/quality03",
        "relaxation/quality04",
        "relaxation/staged",
        "population-analysis/bader-matproj",
        "population-analysis/elf-matproj",
        "band-structure/matproj",
        "density-of-states/matproj",
        "dynamics/mit",
        "diffusion/all-paths",
        "diffusion/from-endpoints",
        "diffusion/from-images",
        "diffusion/single-path",
        "customized/vasp",
    ]


def test_list_of_workflows_by_type():

    assert get_list_of_workflows_by_type("static-energy") == [
        "static-energy/matproj",
        "static-energy/mit",
        "static-energy/neb-endpoint",
        "static-energy/quality04",
    ]

    with pytest.raises(TypeError):
        get_list_of_workflows_by_type("non-existant-type")


def test_get_workflow():

    from simmate.workflows.static_energy import mit_workflow

    assert get_workflow("static-energy/mit") == mit_workflow


def test_get_unique_paramters():
    assert get_unique_parameters() == [
        "command",
        "diffusion_analysis_id",
        "directory",
        "input_parameters",
        "migrating_specie",
        "migration_hop",
        "migration_hop_id",
        "migration_images",
        "nsteps",
        "source",
        "structure",
        "supercell_end",
        "supercell_start",
        "temperature_end",
        "temperature_start",
        "time_step",
        "updated_settings",
        "use_previous_directory",
        "workflow_base",
    ]


@pytest.mark.django_db
def test_load_results_from_directories(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="",  # copy over the entire folder
    )

    load_results_from_directories(base_directory=tmpdir)


def test_parse_parameters(mocker):

    # -------
    # We don't want to actually call these methods, but just ensure that they
    # have been called.
    from simmate.toolkit import Structure
    from simmate.toolkit.diffusion import MigrationHop

    mocker.patch.object(
        Structure,
        "from_dynamic",
    )
    mocker.patch.object(
        MigrationHop,
        "from_dynamic",
    )
    # -------

    example_parameters = {
        "migration_hop": None,
        "supercell_start": None,
        "supercell_end": None,
        "structures": "None; None; None",
    }

    parse_parameters(**example_parameters)
