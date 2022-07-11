# -*- coding: utf-8 -*-

import os
import yaml

from prefect.states import Completed

from simmate.calculators.vasp.inputs import Potcar
from simmate.workflow_engine import Workflow

from simmate.command_line.workflows import workflows
from simmate.conftest import make_dummy_files


def test_workflows_list_all(command_line_runner):
    # list the workflows
    result = command_line_runner.invoke(workflows, ["list-all"])
    assert result.exit_code == 0


def test_workflows_show_config(command_line_runner):

    # list the config for one workflow
    result = command_line_runner.invoke(
        workflows,
        ["show-config", "static-energy.vasp.mit"],
    )
    assert result.exit_code == 0

    # ensure failure when a nested workflow is given
    result = command_line_runner.invoke(
        workflows,
        ["show-config", "relaxation.vasp.staged"],
    )
    assert result.exit_code == 1

    # ensure the flow fails when a incorrect name is given
    result = command_line_runner.invoke(
        workflows,
        ["show-config", "non-existant-flow"],
    )
    assert result.exit_code == 1


def test_workflows_explore(command_line_runner):

    # Make sure it passes when args match
    result = command_line_runner.invoke(
        workflows,
        ["explore"],
        input="6\n2\n",  # gives 6 and then 2 for prompts
    )
    assert result.exit_code == 0

    # Make sure it fails when args don't match
    result = command_line_runner.invoke(
        workflows,
        ["explore"],
        input="1\n99\n",  # gives 1 and then 99 for prompts
    )
    assert result.exit_code == 1


def test_workflows_setup_only(command_line_runner, structure, mocker, tmpdir):

    # establish filenames
    cif_filename = os.path.join(tmpdir, "test.cif")
    new_dirname = os.path.join(tmpdir, "inputs")

    # TODO: switch out the tested workflow for one that doesn't require
    # VASP. As-is, I need to pretend to add a POTCAR file
    potcar_filename = os.path.join(new_dirname, "POTCAR")
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        [
            "setup-only",
            "static-energy.vasp.mit",
            "--structure",
            cif_filename,
            "--directory",
            new_dirname,
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(new_dirname)

    # ensure failure when a nested workflow is given
    result = command_line_runner.invoke(
        workflows,
        ["setup-only", "relaxation.vasp.staged", cif_filename],
    )
    assert result.exit_code == 1


def test_workflows_run(command_line_runner, structure, mocker, tmpdir):

    # establish filenames
    cif_filename = os.path.join(tmpdir, "test.cif")
    new_dirname = os.path.join(tmpdir, "inputs")

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run",
        return_value=Completed(),
    )

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        [
            "run",
            "static-energy.vasp.mit",
            "--structure",
            cif_filename,
            "--directory",
            new_dirname,
        ],
    )
    assert result.exit_code == 0
    Workflow.run.assert_called_with(
        structure=cif_filename,
        directory=new_dirname,
    )

    # ensure failure on improperly matched kwargs
    result = command_line_runner.invoke(
        workflows,
        ["run", "static-energy.vasp.mit", "hangingkwarg"],
    )
    assert result.exit_code == 1


def test_workflows_run_cloud(command_line_runner, structure, mocker, tmpdir):

    # establish filenames
    cif_filename = os.path.join(tmpdir, "test.cif")
    new_dirname = os.path.join(tmpdir, "inputs")

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run_cloud",
        return_value=Completed(),
    )

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        [
            "run-cloud",
            "static-energy.vasp.mit",
            "--structure",
            cif_filename,
            "--directory",
            new_dirname,
        ],
    )
    assert result.exit_code == 0
    Workflow.run_cloud.assert_called_with(
        structure=cif_filename,
        directory=new_dirname,
    )


def test_workflows_run_yaml(command_line_runner, structure, mocker, tmpdir):

    # establish filenames
    cif_filename = os.path.join(tmpdir, "test.cif")
    yaml_filename = os.path.join(tmpdir, "test.yaml")
    new_dirname = os.path.join(tmpdir, "inputs")

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # write the yaml file with our input args
    input_args = dict(
        structure=cif_filename,
        workflow_name="static-energy.vasp.mit",
        directory=new_dirname,
    )
    with open(yaml_filename, "w") as file:
        yaml.dump(input_args, file)

    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run",
        return_value=Completed(),
    )

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        ["run-yaml", yaml_filename],
    )
    assert result.exit_code == 0
    Workflow.run.assert_called_with(
        structure=cif_filename,
        directory=new_dirname,
    )

    # TODO: other yaml files to test with I would like to test these but the
    # current issues is that they are reliant on a vasp command. Maybe I need
    # to mock a lower level method like S3Task.run...?

    # A customized workflow
    """
    # Indicates we want to change the settings, using a specific workflow as a starting-point
    workflow_name: customized/vasp
    workflow_base: static-energy/mit
    
    # These would update the class attributes for the single workflow run
    # The "custom__" start indicates we are updating some attribute
    custom__incar: 
        ENCUT: 600
        KSPACING: 0.25
        MAGMOM: 0.9
    custom__potcar_mappings:
        Y: Y_sv
    
    # Then the remaining inputs are the same as the workflow_base
    structure: Y2CF2.cif
    command: mpirun -n 5 vasp_std > vasp.out
    """

    # From structure file
    """
    workflow_name: static-energy/mit
    structure: Y2CF2.cif
    command: mpirun -n 5 vasp_std > vasp.out
    """

    # From database structure
    """
    workflow_name: static-energy/mit
    structure:
        database_table: MITStaticEnergy
        database_id: 1
    command: mpirun -n 5 vasp_std > vasp.out
    """

    # Nested workflow
    """
    workflow_name: electronic-structure/matproj
    structure: Y2CF2.cif
    command: mpirun -n 5 vasp_std > vasp.out
    """
