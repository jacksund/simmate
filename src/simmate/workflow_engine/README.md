# Simmate Workflow Engine

This module serves two purposes:
1. it helps you define common workflow tasks (for advanced users)
2. it helps you configure your computational resources to run those workflows

### Defining Common Workflow Tasks
For this, jump to the `tasks` submodule. Here you will find base classes that enable things like error handling and job restarts. This is really only meant for advanced users that want to write their own workflows from scratch. Beginners should instead start by checking if there is already a workflow built for them (in `simmate.workflows`) or if there are common tasks already built for the program they are using (for example, VASP users can check `simmate.calculators.vasp`)

### Configuring your Computational Resources

Setting up your computational resources is arguably the most difficult part about using Simmate, and this is because everyone has different resources available. For this reason, we break everything down by use-case below. 
> :warning: If you need help setting up, be sure to reach out to our team! We can even set up a meeting and get you started. Don't hesistate to ask, even if your lab has never tried out compuation before. Just send an email to jacksund@live.unc.edu.


# Running everything on your personal computer

### In serial (one item at time)
This is the easiest case because you actually don't need to set up anything. You can just run your workflows directly with...
```python
from simmate.workflows import example_workflow
result = example_workflow.run()
```

### In parallel (many workflows at once)
To use your entire computer and all of its CPUs, we recommend using Dask. There's one added thing you need to do though -- and that's make sure all of Dask workers are able to connect to the Simmate database. This example let's you submit a bunch of workflows and multiple workflows can run at the same time. You can do this with...
```python
# first setup Dask so that it can connect to Simmate
from dask.distributed import Client
client = Client(preload="simmate.configuration.dask.connect_to_database")

# now submit your workflow and wait for it to finish
future = client.submit(example_workflow.run)
result = future.result()
```

### In parallel (many tasks from a single workflow at once)
 But what if you want to run a single workflow with all of it's tasks in parallel? To do that, we use...
```python
# first setup Dask so that it can connect to Simmate
from dask.distributed import Client
client = Client(preload="simmate.configuration.dask.connect_to_database")

# Tell Prefect that we should submit each task to Dask
from prefect.executors import DaskExecutor
example_workflow.executor = DaskExecutor(address=client.scheduler.address)

# now run your workflow and wait for it to finish
result = example_workflow.run()
```

# Running calculations on external computers

### A single computer located elsewhere

### A University, Federal, or Private HPC Cluster

### Private Cloud Computing

NOTES: I need to consider a few different scenarios. I may stage them to help teach the users.
1. Using Simmate's minimal executor and workers to understand how these all work
2. Using Dask executor. The key difference is that the scheduler is a running process, not a database. Therefore connecting to the scheduler can be more difficult on University clusters (bc of firewalls).
3. Setting up a dask executor with SLURM or some jobqueue
4. Connecting a prefect agent to a dask cluster. This enables advanced monitoring and job submission from anywhere -- but can cause problems with developmental workflows (bc we need to register them). In the future, simmate may solve this problem by having stable APIs or instructing users how to configure custom Prefect workflows with a new Storage class.
