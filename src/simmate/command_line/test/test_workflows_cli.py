# -*- coding: utf-8 -*-

import yaml

from simmate.calculators.vasp.inputs import Potcar
from simmate.command_line.workflows import workflows_app
from simmate.conftest import make_dummy_files
from simmate.workflow_engine import Workflow
from simmate.workflow_engine.workflow import DummyState


def test_workflows_list_all(command_line_runner):
    # list the workflows
    result = command_line_runner.invoke(workflows_app, ["list-all"])
    assert result.exit_code == 0


def test_workflows_show_config(command_line_runner):

    # list the config for one workflow
    result = command_line_runner.invoke(
        workflows_app,
        ["show-config", "static-energy.vasp.mit"],
    )
    assert result.exit_code == 0

    # ensure the flow fails when a incorrect name is given
    result = command_line_runner.invoke(
        workflows_app,
        ["show-config", "non-existant-flow"],
    )
    assert result.exit_code == 1


def test_workflows_explore(command_line_runner):

    # Make sure it passes when args match
    result = command_line_runner.invoke(
        workflows_app,
        ["explore"],
        input="6\n2\n1\n",  # gives 6, 2, and 1 for prompts
    )
    assert result.exit_code == 0

    # Make sure it fails when args don't match
    result = command_line_runner.invoke(
        workflows_app,
        ["explore"],
        input="99\n99\n",  # gives 99 and then 99 for prompts
    )
    assert result.exit_code == 2


def test_workflows_setup_only(command_line_runner, structure, mocker, tmp_path):

    # establish filenames
    cif_filename = str(tmp_path / "test.cif")
    new_dirname = tmp_path / "inputs"  # changed to str below

    # TODO: switch out the tested workflow for one that doesn't require
    # VASP. As-is, I need to pretend to add a POTCAR file
    potcar_filename = new_dirname / "POTCAR"
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # now try writing input files to the tmp_path
    result = command_line_runner.invoke(
        workflows_app,
        [
            "setup-only",
            "static-energy.vasp.mit",
            "--structure",
            cif_filename,
            "--directory",
            str(new_dirname),
        ],
    )
    assert result.exit_code == 0
    assert new_dirname.exists()

    # ensure failure when a nested workflow is given
    result = command_line_runner.invoke(
        workflows_app,
        ["setup-only", "relaxation.vasp.staged", cif_filename],
    )
    assert result.exit_code == 2


def test_workflows_run(command_line_runner, structure, mocker, tmp_path):

    # establish filenames
    cif_filename = str(tmp_path / "test.cif")
    new_dirname = str(tmp_path / "inputs")

    # write the structure to file to be used
    structure.to("cif", cif_filename)

    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run",
        return_value=DummyState(None),
    )
    # the code above can be modified for a prefect executor
    # from prefect.states import Completed
    # return_value=Completed(),

    # now try writing input files to the tmp_path
    result = command_line_runner.invoke(
        workflows_app,
        [
            "run-quick",
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
        workflows_app,
        ["run", "static-energy.vasp.mit", "hangingkwarg"],
    )
    assert result.exit_code == 2


def test_workflows_run_yaml(command_line_runner, structure, mocker, tmp_path):

    # establish filenames
    cif_filename = str(tmp_path / "test.cif")
    yaml_filename = str(tmp_path / "test.yaml")
    new_dirname = str(tmp_path / "inputs")

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
        return_value=DummyState(None),
    )
    # the code above can be modified for a prefect executor
    # from prefect.states import Completed
    # return_value=Completed(),

    # now try writing input files to the tmp_path
    result = command_line_runner.invoke(
        workflows_app,
        ["run", yaml_filename],
    )
    assert result.exit_code == 0
    Workflow.run.assert_called_with(
        structure=cif_filename,
        directory=new_dirname,
    )

    # --------------
    # Testing run-cloud
    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run_cloud",
        return_value=DummyState(None),
    )
    # the code above can be modified for a prefect executor
    # from prefect.states import Completed
    # return_value=Completed(),

    # now try writing input files to the tmp_path
    result = command_line_runner.invoke(
        workflows_app,
        ["run-cloud", yaml_filename],
    )
    assert result.exit_code == 0
    Workflow.run_cloud.assert_called_with(
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
