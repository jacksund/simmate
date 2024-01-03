# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.engine import Workflow
from simmate.workflows.utilities import (
    get_all_workflow_names,
    get_all_workflow_types,
    get_apps_by_type,
    get_unique_parameters,
    get_workflow,
    get_workflow_names_by_type,
    load_results_from_directories,
)


def test_get_workflow_types():
    assert get_all_workflow_types() == [
        # "cluster-expansion",
        # "bad-elf-analysis",
        "customized",
        "diffusion",
        "dynamics",
        "electronic-structure",
        # "nested",
        "population-analysis",
        "relaxation",
        "restart",
        "static-energy",
        "structure-prediction",
    ]


def test_list_of_all_workflows():
    assert get_all_workflow_names() == [
        # "cluster-expansion.clease.bulk-structure",
        # "bad-elf-analysis.badelf.badelf",
        # "bad-elf-analysis.badelf.badelf-hse",
        # "bad-elf-analysis.badelf.badelf-pbesol",
        "customized.toolkit.user-config",
        "diffusion.vasp.neb-all-paths-mit",
        # "diffusion.vasp.neb-all-paths-warren-lab",
        # "diffusion.vasp.neb-all-paths-warren-lab-quick",
        "diffusion.vasp.neb-from-endpoints-mit",
        "diffusion.vasp.neb-from-images-mit",
        "diffusion.vasp.neb-from-images-mvl-ci",
        "diffusion.vasp.neb-single-path-mit",
        "dynamics.vasp.matproj",
        "dynamics.vasp.mit",
        "dynamics.vasp.mvl-npt",
        "electronic-structure.vasp.matproj-band-structure",
        "electronic-structure.vasp.matproj-band-structure-hse",
        "electronic-structure.vasp.matproj-density-of-states",
        "electronic-structure.vasp.matproj-density-of-states-hse",
        "electronic-structure.vasp.matproj-full",
        "electronic-structure.vasp.matproj-hse-full",
        # "nested.vasp.warren-lab-relaxation-static-hse-hse",
        # "nested.vasp.warren-lab-relaxation-static-pbe-hse",
        # "nested.vasp.warren-lab-relaxation-static-pbe-pbe",
        "population-analysis.bader.badelf",
        "population-analysis.bader.bader",
        "population-analysis.bader.bader-dev",
        "population-analysis.bader.combine-chgcars",
        "population-analysis.vasp-bader.badelf-matproj",
        "population-analysis.vasp-bader.bader-matproj",
        "population-analysis.vasp.elf-matproj",
        # "relaxation.vasp.cluster-high-q",
        # "relaxation.vasp.cluster-low-q",
        "relaxation.vasp.matproj",
        "relaxation.vasp.matproj-hse",
        "relaxation.vasp.matproj-hsesol",
        "relaxation.vasp.matproj-metal",
        "relaxation.vasp.matproj-pbesol",
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
        # "relaxation.vasp.warren-lab-hse",
        # "relaxation.vasp.warren-lab-hse-with-wavecar",
        # "relaxation.vasp.warren-lab-hsesol",
        # "relaxation.vasp.warren-lab-pbe",
        # "relaxation.vasp.warren-lab-pbe-metal",
        # "relaxation.vasp.warren-lab-pbe-with-wavecar",
        # "relaxation.vasp.warren-lab-pbesol",
        # "relaxation.vasp.warren-lab-scan",
        # "relaxation.vasp.staged-cluster",
        "restart.toolkit.automatic",
        # "static-energy.vasp.cluster-high-qe",
        "static-energy.quantum-espresso.quality00",
        "static-energy.vasp.matproj",
        "static-energy.vasp.matproj-hse",
        "static-energy.vasp.matproj-hsesol",
        "static-energy.vasp.matproj-pbesol",
        "static-energy.vasp.matproj-scan",
        "static-energy.vasp.mit",
        "static-energy.vasp.mvl-neb-endpoint",
        "static-energy.vasp.prebadelf-matproj",
        "static-energy.vasp.prebader-matproj",
        "static-energy.vasp.quality04",
        # "static-energy.vasp.warren-lab-hse",
        # "static-energy.vasp.warren-lab-hsesol",
        # "static-energy.vasp.warren-lab-pbe",
        # "static-energy.vasp.warren-lab-pbe-metal",
        # "static-energy.vasp.warren-lab-pbesol",
        # "static-energy.vasp.warren-lab-prebadelf-hse",
        # "static-energy.vasp.warren-lab-prebadelf-pbesol",
        # "static-energy.vasp.warren-lab-scan",
        "structure-prediction.toolkit.chemical-system",
        "structure-prediction.toolkit.fixed-composition",
        "structure-prediction.toolkit.new-individual",
        "structure-prediction.toolkit.variable-nsites-composition",
    ]


def test_list_of_apps_by_type():
    assert get_apps_by_type("static-energy") == ["quantum-espresso", "vasp"]

    with pytest.raises(TypeError):
        get_apps_by_type("non-existant-type")


def test_list_of_workflows_by_type():
    assert get_workflow_names_by_type("static-energy") == [
        "static-energy.quantum-espresso.quality00",
        # "static-energy.vasp.cluster-high-qe",
        "static-energy.vasp.matproj",
        "static-energy.vasp.matproj-hse",
        "static-energy.vasp.matproj-hsesol",
        "static-energy.vasp.matproj-pbesol",
        "static-energy.vasp.matproj-scan",
        "static-energy.vasp.mit",
        "static-energy.vasp.mvl-neb-endpoint",
        "static-energy.vasp.prebadelf-matproj",
        "static-energy.vasp.prebader-matproj",
        "static-energy.vasp.quality04",
        # "static-energy.vasp.warren-lab-hse",
        # "static-energy.vasp.warren-lab-hsesol",
        # "static-energy.vasp.warren-lab-pbe",
        # "static-energy.vasp.warren-lab-pbe-metal",
        # "static-energy.vasp.warren-lab-pbesol",
        # "static-energy.vasp.warren-lab-prebadelf-hse",
        # "static-energy.vasp.warren-lab-prebadelf-pbesol",
        # "static-energy.vasp.warren-lab-scan",
    ]

    assert (
        get_workflow_names_by_type(
            "static-energy",
            app_name="non-existant",
        )
        == []
    )

    with pytest.raises(TypeError):
        get_workflow_names_by_type("non-existant-type")


def test_get_workflow():
    from simmate.apps.materials_project.workflows import (
        StaticEnergy__Vasp__Matproj as workflow,
    )

    assert get_workflow("static-energy.vasp.matproj") == workflow


# This is for the test below on custom workflows
WORKFLOW_SCRIPT = """
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):

    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

my_workflow = Example__Python__MyFavoriteSettings
"""


def test_get_custom_workflow(tmp_path):
    script_name = tmp_path / "my_script.py"

    with script_name.open("w") as file:
        file.write(WORKFLOW_SCRIPT)

    workflow = get_workflow(f"{script_name}:my_workflow")

    assert issubclass(workflow, Workflow)


def test_get_unique_paramters():
    assert get_unique_parameters() == [
        "angle_tolerance",
        "atoms_to_print",
        "best_survival_cutoff",
        "charge_file",
        "chemical_system",
        "command",
        "composition",
        "compress_output",
        "convergence_cutoff",
        "diffusion_analysis_id",
        "directory",
        "directory_new",
        "directory_old",
        "empty_ion",
        "empty_sites",
        "fitness_field",
        "input_parameters",
        "is_restart",
        "max_atoms",
        "max_path_length",
        "max_stoich_factor",
        "max_structures",
        "max_supercell_atoms",
        "migrating_specie",
        "migration_hop",
        "migration_images",
        "min_atoms",
        "min_length",
        "min_structures_exact",
        "min_supercell_atoms",
        "min_supercell_vector_lengths",
        "nfirst_generation",
        "nimages",
        "nsteadystate",
        "nsteps",
        "partitioning_file",
        "percolation_mode",
        "relax_bulk",
        "relax_endpoints",
        "run_id",
        "search_id",
        "selector_kwargs",
        "selector_name",
        "singleshot_sources",
        "sleep_step",
        "source",
        "species_to_print",
        "standardize_structure",
        "steadystate_source_id",
        "steadystate_sources",
        "structure",
        "subworkflow_kwargs",
        "subworkflow_name",
        "supercell_end",
        "supercell_start",
        "symmetry_precision",
        "temperature_end",
        "temperature_start",
        "time_step",
        "updated_settings",
        "vacancy_mode",
        "validator_kwargs",
        "validator_name",
        "workflow_base",
        "write_summary_files",
    ]


@pytest.mark.django_db
def test_load_results_from_directories(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="",  # copy over the entire folder
    )

    load_results_from_directories(base_directory=tmp_path)
