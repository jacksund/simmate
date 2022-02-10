# -*- coding: utf-8 -*-

import os
import shutil

from prefect.engine.state import Success

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
        ["show-config", "static-energy/mit"],
    )
    assert result.exit_code == 0

    # ensure failure when a nested workflow is given
    result = command_line_runner.invoke(
        workflows,
        ["show-config", "relaxation/staged"],
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
        input="1\n2\n",  # gives 1 and then 2 for prompts
    )
    assert result.exit_code == 0

    # Make sure it fails when args don't match
    result = command_line_runner.invoke(
        workflows,
        ["explore"],
        input="1\n99\n",  # gives 1 and then 99 for prompts
    )
    assert result.exit_code == 1


def test_workflows_setup_only(command_line_runner, structure, mocker):

    #####
    # TODO: switch out the tested workflow for one that doesn't require
    # VASP. As-is, I need to pretend to add a POTCAR file
    from simmate.calculators.vasp.inputs import Potcar

    potcar_filename = os.path.join("MIT_Static_Energy_inputs", "POTCAR")
    Potcar.to_file_from_type = mocker.MagicMock(
        return_value=make_dummy_files(potcar_filename)
    )
    #####

    # write the structure to file to be used
    structure.to("cif", "test.cif")

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        ["setup-only", "static-energy/mit", "test.cif"],
    )
    assert result.exit_code == 0
    assert os.path.exists("MIT_Static_Energy_inputs")

    # remove the folder
    shutil.rmtree("MIT_Static_Energy_inputs")

    # ensure failure when a nested workflow is given
    result = command_line_runner.invoke(
        workflows,
        ["setup-only", "relaxation/staged", "test.cif"],
    )
    assert result.exit_code == 1

    # remove the structure file
    os.remove("test.cif")


def test_workflows_run(command_line_runner, structure, mocker):

    # write the structure to file to be used
    structure.to("cif", "test.cif")

    #####
    # I don't want to actually run the workflow, so I override the run method
    from simmate.workflows.static_energy import mit_workflow

    mit_workflow.run = mocker.MagicMock(return_value=Success())
    #####

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        ["run", "static-energy/mit", "-s", "test.cif"],
    )
    assert result.exit_code == 0
    mit_workflow.run.assert_called_with(
        structure=structure,
        directory=None,
    )

    # remove the structure file
    os.remove("test.cif")

    # ensure failure on improperly matched kwargs
    result = command_line_runner.invoke(
        workflows,
        ["run", "static-energy/mit", "hangingkwarg"],
    )
    assert result.exit_code == 1


def test_workflows_run_cloud(command_line_runner, structure, mocker):

    # write the structure to file to be used
    structure.to("cif", "test.cif")

    #####
    # I don't want to actually run the workflow, so I override the run method
    from simmate.workflows.static_energy import mit_workflow

    mit_workflow.run_cloud = mocker.MagicMock(return_value=Success())
    #####

    # now try writing input files to the tmpdir
    result = command_line_runner.invoke(
        workflows,
        ["run-cloud", "static-energy/mit", "test.cif"],
    )
    assert result.exit_code == 0
    mit_workflow.run_cloud.assert_called_with(
        structure=structure,
        directory=None,
    )

    # remove the structure file
    os.remove("test.cif")
