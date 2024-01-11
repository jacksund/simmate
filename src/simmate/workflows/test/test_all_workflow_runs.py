# -*- coding: utf-8 -*-

import logging

import pytest

from simmate.workflows.utilities import get_all_workflow_names, get_workflow


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
        workflow_name = "customized.toolkit.user-config"
        workflow = get_workflow(workflow_name)
        state = workflow.run(
            workflow_base="relaxation.vasp.quality00",
            input_parameters={
                "structure": structure,
                "command": "mpirun -n 14 vasp_std > vasp.out",
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
            "relaxation.vasp.warren-lab-hse",
            "relaxation.vasp.warren-lab-hse-with-wavecar",
            "relaxation.vasp.warren-lab-hsesol",
            "relaxation.vasp.warren-lab-pbe",
            "relaxation.vasp.warren-lab-pbe-metal",
            "relaxation.vasp.warren-lab-pbe-with-wavecar",
            "relaxation.vasp.warren-lab-pbesol",
            "relaxation.vasp.warren-lab-scan",
            "static-energy.vasp.matproj",
            "static-energy.vasp.mit",
            "static-energy.vasp.mvl-neb-endpoint",
            "static-energy.vasp.quality04",
            "static-energy.vasp.matproj-hse",  # slow
            "static-energy.vasp.matproj-scan",  # slow
            "static-energy.vasp.warren-lab-hse",
            "static-energy.vasp.warren-lab-hsesol",
            "static-energy.vasp.warren-lab-pbe",
            "static-energy.vasp.warren-lab-pbe-metal",
            "static-energy.vasp.warren-lab-pbesol",
            "static-energy.vasp.warren-lab-prebadelf-hse",
            "static-energy.vasp.warren-lab-prebadelf-pbesol",
            "static-energy.vasp.warren-lab-scan",
            "population-analysis.vasp-bader.bader-matproj",
            "population-analysis.vasp.elf-matproj",
            "electronic-structure.vasp.matproj-full",
            "electronic-structure.vasp.matproj-hse-full",  # slow
        ]
        for workflow_name in s3_flows:
            workflow = get_workflow(workflow_name)
            state = workflow.run(
                structure=structure,
                command="mpirun -n 14 vasp_std > vasp.out",
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
                command="mpirun -n 14 vasp_std > vasp.out",
                nsteps=50,
                temperature_start=400,
                temperature_end=400,
            )
            if state.is_completed():
                successful_flows.append(workflow_name)

        # TEST NEB FLOWS
        # For diffusion, we look at I- diffusion in Y2CI2 (takes roughly 1 hr)
        structure = sample_structures["Y2CI2_mp-1206803_primitive"]
        workflow_name = "diffusion.vasp.neb-all-paths-mit"
        workflow = get_workflow(workflow_name)
        state = workflow.run(
            structure=structure,
            migrating_specie="I",
            command="mpirun -n 14 vasp_std > vasp.out",
            nimages=1,
            min_atoms=10,
            max_atoms=25,
            min_length=4,
        )
        state.result()
        if state.is_completed():
            successful_flows.append(workflow_name)

        # TEST BadELF FLOWS
        structure = sample_structures["Ca2N_mp-2686_primitive"]
        workflow_name = "bad-elf-analysis.badelf.badelf-test"
        workflow = get_workflow(workflow_name)

        # This workflow runs a static energy and then badelf calculation. The
        # hse version is identical, but uses a different static energy step
        # which is tested above. However, there are 3 different algorithms
        # which can be used for partitioning, each of which needs to be tested
        algorithms = ["badelf", "voronelf", "zero-flux"]
        for algorithm in algorithms:
            state = workflow.run(
                structure=structure,
                command="mpirun -n 14 vasp_std > vasp.out",
                algorithm=algorithm,
                cores=14,
                check_for_covalency=False,
            )
            state.result()
            if state.is_completed():
                successful_flows.append(workflow_name)

    # check which flows either (1) failed or (2) weren't tested
    all_flows = get_all_workflow_names()
    missing_failed_flows = list(set(all_flows) - set(successful_flows))
    missing_failed_flows.sort()

    logging.info(
        f"The following workflows either failed or were not tested: {missing_failed_flows}"
    )
    # assert missing_failed_flows == []
