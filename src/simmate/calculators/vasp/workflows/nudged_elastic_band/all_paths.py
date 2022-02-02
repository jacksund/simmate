# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.calculators.vasp.workflows.relaxation import (
    mit_workflow as relaxation_mit_workflow,
    neb_endpoint_workflow as relaxation_neb_endpoint_workflow,
)

from simmate.calculators.vasp.workflows.energy import (
    mit_workflow as energy_mit_workflow,
)

# Convert our workflow objects to task objects
relax_bulk = relaxation_mit_workflow.to_workflow_task()
energy_bulk = energy_mit_workflow.to_workflow_task()
relax_endpoint = relaxation_neb_endpoint_workflow.to_workflow_task()


with Workflow("Full NEB Analysis") as workflow:

    structure = Parameter("structure")
    structure = Parameter("structure")

    # I separate these out because each calculation is a very different scale.
    # For example, you may want to run the bulk relaxation on 10 cores, the
    # supercell on 50, and the NEB on 200. Even though more cores are available,
    # running smaller calculation on more cores could slow down the calc.
    command_bulk = Parameter("command_bulk", default="vasp_std > vasp.out")
    command_supercell = Parameter("command_supercell", default="vasp_std > vasp.out")
    command_neb = Parameter("command_neb", default="vasp_std > vasp.out")

    # Our step is to run a relaxation on the bulk structure and it uses our inputs
    # directly. The remaining one tasks pass on results.
    run_id_00 = relax_bulk(
        structure=structure,
        command=command_bulk,
    )

    # A static energy calculation on the relaxed structure. This isn't necessarily
    # required for NEB, but it takes very little time and let's us link the
    # NEB analysis to a specific structure table.
    run_id_01 = energy_bulk(
        structure={
            "calculation_table": "MITRelaxation",
            "directory": run_id_00["directory"],
            "structure_field": "structure_final",
        },
        command=command_bulk,
    )

    # This step does NOT run any calculation, but instead, identifies all
    # diffusion pathways and builds the necessary database entries.
    # TODO.
