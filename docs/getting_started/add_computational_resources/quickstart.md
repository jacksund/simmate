# Distributed Computational Resources

## Quickstart

This guide shows you how to submit jobs to a queue and start multiple workers to process them.

!!! warning "Database Requirement"
    If you followed the previous tutorial, you should already be on a **Postgres database**. 

    If you are still using the default **SQLite** database, you **cannot** run multiple workers at once. SQLite will crash if more than one process tries to write to it. For parallel workflows, ensure you've set up a cloud database (like Postgres).

### 1. Match Your Config
If you are using multiple computers, ensure they are all connected to the same database:
``` bash
simmate config show --user-only
```

### 2. Submit a Job
Switch from the `run` command to `run-cloud`. This "schedules" the workflow in your database rather than running it immediately.
``` bash
# example.yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: NaCl.cif
```
``` bash
simmate workflows run-cloud example.yaml
```

### 3. Start One Worker
Before starting a full cluster, try starting a single worker to process your job. This worker will stay "on duty" until you stop it (Ctrl+C).
``` bash
simmate compute start-worker
```

### 4. Start a Cluster
Once you're comfortable with one worker, you can start a cluster of workers to process many jobs at once. On your local machine, this command starts 3 workers that will run in parallel:
``` bash
simmate compute start-cluster 3 --type local
```

### 5. HPC Clusters (Optional)
If you are on a SLURM cluster, you can submit workers to the cluster queue directly. 

!!! note
    The `slurm` cluster type requires a `submit.sh` file to be present in your current directory. Simmate uses this file as a template to submit multiple workers to the queue.

``` bash
# Submits 3 workers to the SLURM queue using submit.sh
simmate compute start-cluster 3 --type slurm
```

!!! tip "Single-Flow Workers"
    On some HPC clusters, it's better to start a worker that runs **one** job and then shuts down. This helps with resource allocation. Your `submit.sh` would then look like this:
    ```bash
    #!/bin/bash
    # (Your SBATCH settings here...)
    simmate compute start-singleflow-worker
    ```

### 6. Monitor Your Jobs
You can check the status of your submitted jobs at any time:
```bash
simmate compute stats
```

For more details on managing clusters and monitoring jobs, see the **Full Guides** on Compute.
