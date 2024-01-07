# Should I Establish My Own Cluster?

!!! note
    We recognize that resource limitations can be stringent across labs and companies, making resource sharing unfeasible, even in close collaborations. Simmate addresses this by facilitating the sharing of a cloud database *without* the need to share computational resources. This means you can contribute to a shared database without exposing your computational resources to others.

-------------------------------------------------------------------------------

## Basic Resource Utilization

Each team will likely manage their own computational resources, which could include:

- A university or federal HPC cluster with SLURM, PBS, or another queue system
- A single node or a Kubernetes cluster on a cloud provider
- A collection of shared desktop computers within your lab
- Any combination of these resources

The simplest way to utilize these resources is to log in and execute a simmate workflow using the `run` method. This action runs the workflow directly on your resource. 

This was demonstrated in the "Run a workflow" tutorial when we executed `simmate workflows run ...`. On an HPC SLURM cluster, simmate would be run using a `submit.sh`:

```
#!/bin/bash

#SBATCH --output=slurm.out
#SBATCH --nodes=1
#SBATCH --ntasks=2

simmate workflows run-yaml my_settings.yaml > simmate.out
```

!!! tip 
    If you're only executing a few workflows per day (<10), we recommend sticking to this method of running workflows. In other words, just execute `simmate workflows run`. Avoid unnecessary complexity. Revisit tutorial 02 to refresh these concepts.

-------------------------------------------------------------------------------

## When to Establish Workers

If your team is submitting hundreds or thousands of workflows simultaneously, it would be highly beneficial to monitor and manage these workflows using a **scheduler** and **cluster**. 

Similar to our cloud database in the previous tutorial, you only need **ONE** person to manage **ALL** of your computational resources. Once the resources are established, other users can connect using the database connection file (or an API key if you're using Prefect).

If you're the designated person for your team, proceed with this tutorial. If not, consult with your point person! Utilizing your team's resources should be as simple as switching from the `run` to `run_cloud` method.

-------------------------------------------------------------------------------