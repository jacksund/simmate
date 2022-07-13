# -*- coding: utf-8 -*-

import pytest

from simmate.workflows.utilities import (
    get_list_of_all_workflows,
    get_workflow,
)


@pytest.mark.vasp
@pytest.mark.prefect_db
@pytest.mark.django_db
def test_all_workflow_runs(tmpdir, sample_structures):

    # For testing, look at the NaCl rocksalt primitive structure
    structure = sample_structures["NaCl_mp-22862_primitive"]

    with tmpdir.as_cwd():

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
            "electronic-structure.vasp.matproj-full",
            "population-analysis.vasp.bader-matproj",
            "population-analysis.vasp.elf-matproj",
            "relaxation.vasp.matproj",
            "relaxation.vasp.mit",
            "relaxation.vasp.neb-endpoint",
            "relaxation.vasp.quality00",
            "relaxation.vasp.quality01",
            "relaxation.vasp.quality02",
            "relaxation.vasp.quality03",
            "relaxation.vasp.staged",
            "relaxation.vasp.quality04",
            "static-energy.vasp.matproj",
            "static-energy.vasp.mit",
            "static-energy.vasp.neb-endpoint",
            "static-energy.vasp.quality04",
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
        workflow_name = "dynamics.vasp.mit"
        workflow = get_workflow(workflow_name)
        state = workflow.run(
            structure=structure,
            command="mpirun -n 12 vasp_std > vasp.out",
            nsteps=100,
            temperature_start=400,
            temperature_end=400,
        )
        if state.is_completed():
            successful_flows.append(workflow_name)

        # TEST NEB FLOWS
        # For testing, look at I- diffusion in Y2CF2
        # structure = sample_structures["Y2CI2_mp-1206803_primitive"]
        # workflow_name = "diffusion.vasp.neb-all-paths"
        # workflow = get_workflow(workflow_name)
        # state = workflow.run(
        #     structure=structure,
        #     migrating_specie="I",
        #     command="mpirun -n 15 vasp_std > vasp.out",
        #     directory=str(tmpdir),
        # )
        # state.result()
        # if state.is_completed():
        #     successful_flows.append(workflow_name)

    # check which flows either (1) failed or (2) weren't tested
    all_flows = get_list_of_all_workflows()
    missing_failed_flows = list(set(all_flows) - set(successful_flows))
    missing_failed_flows.sort()

    assert missing_failed_flows == [
        "diffusion.vasp.neb-all-paths",
        "diffusion.vasp.neb-from-endpoints",
        "diffusion.vasp.neb-from-images",
        "diffusion.vasp.neb-single-path",
        "population-analysis.vasp.badelf-matproj",
    ]
