# -*- coding: utf-8 -*-

from simmate.compute.launcher import get_container_command, get_container_env


def test_container_command_keeps_secrets_out():
    env = get_container_env("https://simmate.org", "secret")
    assert env == {
        "SIMMATE__CLIENT__HOST": "https://simmate.org",
        "SIMMATE__CLIENT__API_KEY": "secret",
    }

    command = get_container_command("podman", "test", "image:v1", ["simmate"], env)
    assert "secret" not in " ".join(command)
    assert ["--env", "SIMMATE__CLIENT__API_KEY"] == command[
        command.index("SIMMATE__CLIENT__API_KEY") - 1 :
    ][:2]
    assert command[-8:] == [
        "image:v1",
        "simmate",
        "compute",
        "worker",
        "start",
        "--api",
        "--tag",
        "simmate",
    ]
