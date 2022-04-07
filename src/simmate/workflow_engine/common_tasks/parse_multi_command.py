# -*- coding: utf-8 -*-

from prefect import task

from typing import List

# OPTIMIZE: I need to return a dictionary because Prefect struggles to handle
# a list or tuple return in their workflow context. Maybe this will change in
# Prefect Orion though.
@task
def parse_multi_command(command: str, commands_out: List[int]) -> dict:
    """
    Given a list of commands separated by semicolons (;), this simply separates
    the commands into individual ones.

    This is useful for workflows that require different commands at different
    steps in a workflow -- while also not breaking our CLI which expects a
    single command input.

    For example, NEB allows for three unique commands (ncommands_out=3):
        - command_bulk: for relaxing a bulk crystal structure
        - command_endpoint: for relaxing an endpoint supercell structure
        - command_neb: for relaxing a series of supercell structure by NEB

    To run this, the CLI expects these three commands to be strung together.
    ``` bash
    simmate workflows run diffusion/example_neb -c "vasp_std > vasp.out; mpirun -n 10 vasp_std > vasp.out; mpirun -n 50 vasp_std > vasp.out"
    ```

    These would parse into the following subcommands:
        - command_bulk: vasp_std > vasp.out
        - command_endpoint: mpirun -n 10 vasp_std > vasp.out
        - command_neb: mpirun -n 50 vasp_std > vasp.out

    Alternatively, you can provide one single command that will be reproduced
    for all others. For example, this command would use the same command for
    command_bulk, command_endpoint, and command_neb.
    ``` bash
    simmate workflows run diffusion/example_neb -c "vasp_std > vasp.out"
    ```

    #### Parameters

    - `command`:
        The command or list of commands that should be separated into a list.
        If you provide a list of commands, include them in a single string
        where individual commands are separated by semicolons (;)

    - `subcommands`:
        A list of names for each subcommands that should be output. Typically
        this is a fixed parameter for a given workflow and will be hardcoded
        elsewhere -- and therefore never set by a user.
    """

    # separate commands into a python list
    command_list = command.split(";")
    # remove start/end whitespace
    command_list = [c.strip() for c in command_list]

    # If only one command was given, duplicate it in this list for the number
    # of outputs we expect.
    if len(command_list) == 1:
        command_list = command_list * len(commands_out)

    # If we have the proper number of inputs, go ahead and return!
    elif len(command_list) == len(commands_out):
        pass

    # otherwise the user provided the incorrect number of commands
    else:
        raise Exception(
            "Incorrect number of commands provided. Expected either 1 "
            f"or {len(commands_out)}"
        )

    # Convert the commands to dictionary before returning.
    return {key: command for key, command in zip(commands_out, command_list)}
