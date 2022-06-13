# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.workflows.utilities import (
    get_list_of_all_workflows,
    get_list_of_workflows_by_type,
    get_workflow,
    load_results_from_directories,
    get_unique_parameters,
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
        "population-analysis/badelf-matproj",
        "population-analysis/bader-matproj",
        "population-analysis/elf-matproj",
        "population-analysis/prebadelf-matproj",
        "population-analysis/prebader-matproj",
        "band-structure/matproj",
        "density-of-states/matproj",
        "electronic-structure/matproj",
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
        "copy_previous_directory",
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
