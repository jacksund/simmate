# TODO


notes on submitting to cloud...
```python

# Load an example structure
from pymatgen.core.structure import Structure
structure = Structure.from_file("YFeO3_MIT/POSCAR")

# ---------------------------------------------------------

# This is the normal method, which I don't like because you need to look
# up the flow_id from cloud.

from prefect import Client
client = Client()
client.create_flow_run(
    flow_id="33a0624b-5bbd-400a-b038-8dc8cb2d34c9", 
    parameters=dict(
        directory="test-02",
        vasp_command="mpirun -n 4 vasp > vasp.out",
        structure=structure.to_json(),
    ),
    labels=["WarWulf"]
)

# ---------------------------------------------------------

# This the current method I prefer because it let's me just provide a flow name
# and it will look up the most recent version in prefect cloud automatically

from simmate.workflows.relaxation.mit import workflow

from prefect.tasks.prefect.flow_run import create_flow_run

flow_run_id = create_flow_run.run(
    flow_name=workflow.name,
    # project_name="",  # OPTIONAL
    parameters=dict(
        directory="test-03",
        vasp_command="mpirun -n 4 vasp > vasp.out",
        structure=structure.to_json(),
    ),
    labels=["WarWulf"],
)

# ---------------------------------------------------------

# I wrote a custom class to handle submitting workflows to Prefect, or
# running them locally, or even running them within other workflows.

from simmate.workflow_engine.tasks.run_workflow_task import RunWorkflowTask
from simmate.workflows.relaxation.mit import workflow

task = RunWorkflowTask(workflow)

task.run(
    structure=structure,
    directory="nacl_01",
    vasp_command="mpirun -n 4 vasp > vasp.out",
    executor_type="prefect",
    labels=["WarWulf"],
    wait_for_run=False,
)

```
