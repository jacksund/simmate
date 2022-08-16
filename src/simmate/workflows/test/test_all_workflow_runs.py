# -*- coding: utf-8 -*-

import pytest

from simmate.workflows.utilities import get_list_of_all_workflows, get_workflow


# @pytest.mark.prefect_db
@pytest.mark.vasp
@pytest.mark.django_db
def test_all_workflow_runs(tmp_path, sample_structures):

    # For testing, look at the NaCl rocksalt primitive structure
    structure = sample_structures["NaCl_mp-22862_primitive"]

    # -------------
    # https://stackoverflow.com/questions/41742317/
    import contextlib
    import os
    from pathlib import Path

    @contextlib.contextmanager
    def working_directory(path):
        """Changes working directory and returns to previous on exit."""
        prev_cwd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

    # -----------------

    with working_directory(tmp_path):

        successful_flows = []

        # TEST CUSTOMIZED FLOW
        workflow_name = "customized.vasp.user-config"
        workflow = get_workflow(workflow_name)
        state = workflow.run(
            workflow_base="relaxation.vasp.quality00",
            input_parameters={
                "structure": structure,
                "command": "mpirun -n 12 vasp_std > vasp.out",
            },
            updated_settings={
                "incar": {"NPAR": 1, "ENCUT": 600},
            },
        )
        if state.is_completed():
            successful_flows.append(workflow_name)

        # TEST S3Workflows
        s3_flows = [
            "relaxation.vasp.matproj",
            "relaxation.vasp.mit",
            "relaxation.vasp.mvl-neb-endpoint",
            "relaxation.vasp.quality00",
            "relaxation.vasp.quality01",
            "relaxation.vasp.quality02",
            "relaxation.vasp.quality03",
            "relaxation.vasp.quality04",
            "relaxation.vasp.staged",
            "relaxation.vasp.matproj-metal",
            "relaxation.vasp.matproj-scan",  # slow
            "relaxation.vasp.matproj-hse",  # slow
            "relaxation.vasp.mvl-grainboundary",
            "relaxation.vasp.mvl-slab",
            "static-energy.vasp.matproj",
            "static-energy.vasp.mit",
            "static-energy.vasp.mvl-neb-endpoint",
            "static-energy.vasp.quality04",
            "static-energy.vasp.matproj-hse",  # slow
            "static-energy.vasp.matproj-scan",  # slow
            "population-analysis.vasp.bader-matproj",
            "population-analysis.vasp.elf-matproj",
            "electronic-structure.vasp.matproj-full",
            "electronic-structure.vasp.matproj-hse-full",  # slow
        ]
        for workflow_name in s3_flows:

            workflow = get_workflow(workflow_name)
            state = workflow.run(
                structure=structure,
                command="mpirun -n 12 vasp_std > vasp.out",
            )
            if state.is_completed():
                successful_flows.append(workflow_name)

        # TEST MD FLOW
        dynamics_flows = [
            "dynamics.vasp.mit",
            "dynamics.vasp.matproj",
            "dynamics.vasp.mvl-npt",
        ]
        for workflow_name in dynamics_flows:
            workflow = get_workflow(workflow_name)
            state = workflow.run(
                structure=structure,
                command="mpirun -n 12 vasp_std > vasp.out",
                nsteps=50,
                temperature_start=400,
                temperature_end=400,
            )
            if state.is_completed():
                successful_flows.append(workflow_name)

        # TEST NEB FLOWS
        # For testing, look at I- diffusion in Y2CI2 (takes roughly 1 hr)
        structure = sample_structures["Y2CI2_mp-1206803_primitive"]
        workflow_name = "diffusion.vasp.neb-all-paths-mit"
        workflow = get_workflow(workflow_name)
        state = workflow.run(
            structure=structure,
            migrating_specie="I",
            command="mpirun -n 12 vasp_std > vasp.out",
            nimages=1,
            min_atoms=10,
            max_atoms=25,
            min_length=4,
        )
        state.result()
        if state.is_completed():
            successful_flows.append(workflow_name)

    # check which flows either (1) failed or (2) weren't tested
    all_flows = get_list_of_all_workflows()
    missing_failed_flows = list(set(all_flows) - set(successful_flows))
    missing_failed_flows.sort()

    assert missing_failed_flows == [
        "diffusion.vasp.neb-from-endpoints-mit",  # used within all-paths
        "diffusion.vasp.neb-from-images-mit",  # used within all-paths
        "diffusion.vasp.neb-single-path-mit",  # used within all-paths
        "population-analysis.vasp.badelf-matproj",  # requires db
        "restart.simmate.automatic",
    ]
