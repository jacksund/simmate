# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.workflows.utilities import (
    get_list_of_all_workflows,
    get_list_of_workflows_by_type,
    get_unique_parameters,
    get_workflow,
    get_workflow_types,
    load_results_from_directories,
)


def test_get_workflow_types():
    assert get_workflow_types() == [
        "customized",
        "diffusion",
        "dynamics",
        "electronic-structure",
        "population-analysis",
        "relaxation",
        "restart",
        "static-energy",
        "structure-prediction",
    ]


def test_list_of_all_workflows():

    assert get_list_of_all_workflows() == [
        "customized.vasp.user-config",
        "diffusion.vasp.neb-all-paths-mit",
        "diffusion.vasp.neb-from-endpoints-mit",
        "diffusion.vasp.neb-from-images-mit",
        "diffusion.vasp.neb-single-path-mit",
        "dynamics.vasp.matproj",
        "dynamics.vasp.mit",
        "dynamics.vasp.mvl-npt",
        "electronic-structure.vasp.matproj-full",
        "electronic-structure.vasp.matproj-hse-full",
        "population-analysis.vasp.badelf-matproj",
        "population-analysis.vasp.bader-matproj",
        "population-analysis.vasp.elf-matproj",
        "relaxation.vasp.matproj",
        "relaxation.vasp.matproj-hse",
        "relaxation.vasp.matproj-metal",
        "relaxation.vasp.matproj-scan",
        "relaxation.vasp.mit",
        "relaxation.vasp.mvl-grainboundary",
        "relaxation.vasp.mvl-neb-endpoint",
        "relaxation.vasp.mvl-slab",
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
        "relaxation.vasp.quality03",
        "relaxation.vasp.quality04",
        "relaxation.vasp.staged",
        "restart.simmate.automatic",
        "static-energy.vasp.matproj",
        "static-energy.vasp.matproj-hse",
        "static-energy.vasp.matproj-scan",
        "static-energy.vasp.mit",
        "static-energy.vasp.mvl-neb-endpoint",
        "static-energy.vasp.quality04",
        "structure-prediction.python.fixed-composition",
        "structure-prediction.python.new-individual",
    ]


def test_list_of_workflows_by_type():

    assert get_list_of_workflows_by_type("static-energy") == [
        "static-energy.vasp.matproj",
        "static-energy.vasp.matproj-hse",
        "static-energy.vasp.matproj-scan",
        "static-energy.vasp.mit",
        "static-energy.vasp.mvl-neb-endpoint",
        "static-energy.vasp.quality04",
    ]

    with pytest.raises(TypeError):
        get_list_of_workflows_by_type("non-existant-type")


def test_get_workflow():

    from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj as workflow

    assert get_workflow("static-energy.vasp.matproj") == workflow


def test_get_unique_paramters():
    assert get_unique_parameters() == [
        "command",
        "composition",
        "compress_output",
        "copy_previous_directory",
        "diffusion_analysis_id",
        "directory",
        "directory_new",
        "directory_old",
        "fitness_field",
        "input_parameters",
        "is_restart",
        "limit_best_survival",
        "max_atoms",
        "max_structures",
        "migrating_specie",
        "migration_hop",
        "migration_hop_id",
        "migration_images",
        "min_atoms",
        "min_length",
        "nfirst_generation",
        "nimages",
        "nsteadystate",
        "nsteps",
        "pre_sanitize_structure",
        "pre_standardize_structure",
        "run_id",
        "search_id",
        "selector_kwargs",
        "selector_name",
        "singleshot_sources",
        "sleep_step",
        "source",
        "steadystate_sources",
        "structure",
        "structure_source_id",
        "subworkflow_kwargs",
        "subworkflow_name",
        "supercell_end",
        "supercell_start",
        "tags",
        "temperature_end",
        "temperature_start",
        "time_step",
        "updated_settings",
        "validator_kwargs",
        "validator_name",
        "workflow_base",
    ]


@pytest.mark.django_db
def test_load_results_from_directories(tmp_path):

    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="",  # copy over the entire folder
    )

    load_results_from_directories(base_directory=tmp_path)
