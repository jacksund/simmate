# -*- coding: utf-8 -*-

# import os

from simmate.toolkit.diffusion import MigrationHop

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)
from simmate.workflows.common_tasks import (
    LoadInputAndRegister,
    parse_multi_command,
)

from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    get_endpoint_structures,
    get_migration_images_from_endpoints,
)
from simmate.calculators.vasp.workflows.relaxation import (
    neb_endpoint_workflow as relaxation_neb_endpoint_workflow,
)

# Convert our workflow objects to task objects
relax_endpoint = relaxation_neb_endpoint_workflow.to_workflow_task()

# Extra setup tasks
load_input_and_register = LoadInputAndRegister()  # TODO: make DiffusionAnalysis a calc?

with Workflow("NEB (for a single migration hop)") as workflow:

    migration_hop = Parameter("migration_hop")
    directory = Parameter("directory", default=None)
    source = Parameter("source", default=None)

    # I separate these out because each calculation is a very different scale.
    # For example, you may want to run the bulk relaxation on 10 cores, the
    # supercell on 50, and the NEB on 200. Even though more cores are available,
    # running smaller calculation on more cores could slow down the calc.
    command = Parameter("command", default="vasp_std > vasp.out")
    # command list expects three subcommands:
    #   command_bulk, command_supercell, and command_neb
    subcommands = parse_multi_command(
        command,
        commands_out=["command_supercell", "command_neb"],
    )

    # Load our input and make a base directory for all other workflows to run
    # within for us.
    migration_hop_toolkit, directory_cleaned = load_input_and_register(
        input_obj=migration_hop,
        input_class=MigrationHop,
        source=source,
        directory=directory,
    )

    # get the supercell endpoint structures
    supercell_start, supercell_end = get_endpoint_structures(migration_hop_toolkit)

    # Relax the starting supercell structure
    # run_id_00 = relax_endpoint(
    #     structure=supercell_start,
    #     command=subcommands["command_supercell"],
    #     directory=directory_cleaned + os.path.sep + "endpoint_relaxation_start",
    # )

    # Relax the ending supercell structure
    # run_id_01 = relax_endpoint(
    #     structure=supercell_end,
    #     command=subcommands["command_supercell"],
    #     directory=directory_cleaned + os.path.sep + "endpoint_relaxation_end",
    # )

    images = get_migration_images_from_endpoints(
        supercell_start=supercell_start,
        supercell_end=supercell_start,
        # TODO: these should instead be dict objects that grab the output from
        # the relaxation above
    )

    # TODO: picking up here in the morning --> I can now run the NEB task using
    # these images.


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
