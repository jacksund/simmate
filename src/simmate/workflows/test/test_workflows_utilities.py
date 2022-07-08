# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.workflows.utilities import (
    get_workflow_types,
    get_list_of_all_workflows,
    get_list_of_workflows_by_type,
    get_workflow,
    load_results_from_directories,
    get_unique_parameters,
)


def test_get_workflow_types():
    assert get_workflow_types() == [
        "customized",
        "diffusion",
        "dynamics",
        "electronic_structure",
        "population_analysis",
        "relaxation",
        "static_energy",
    ]


def test_list_of_all_workflows():

    assert get_list_of_all_workflows() == [
        "customized.vasp.user-config",
        "diffusion.vasp.neb-all-paths",
        "diffusion.vasp.neb-from-endpoints",
        "diffusion.vasp.neb-from-images",
        "diffusion.vasp.neb-single-path",
        "dynamics.vasp.mit",
        "electronic-structure.vasp.mat-proj-full",
        "population-analysis.vasp.badelf-matproj",
        "population-analysis.vasp.bader-matproj",
        "population-analysis.vasp.elf-matproj",
        "relaxation.vasp.mat-proj",
        "relaxation.vasp.mit",
        "relaxation.vasp.neb-endpoint",
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
        "relaxation.vasp.quality03",
        "relaxation.vasp.quality04",
        "static-energy.vasp.mat-proj",
        "static-energy.vasp.mit",
        "static-energy.vasp.neb-endpoint",
        "static-energy.vasp.quality04",
    ]


def test_list_of_workflows_by_type():

    assert get_list_of_workflows_by_type("static-energy") == [
        "static-energy.vasp.matproj",
        "static-energy.vasp.mit",
        "static-energy.vasp.neb-endpoint",
        "static-energy.vasp.quality04",
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
