
# Should I set up my own cluster?

!!! note
    We understand that resource restrictions can be very stingent between labs and companies. So sharing resources is not possible, even in close collaborations. Simmate addresses this issue by making it easy to share a cloud database *without* sharing computational resources. In other words, you can contribute to a shared database without letting others see/access your computational resources.

-------------------------------------------------------------------------------

## Basic use of resources

Each team will likely need to handle their own computational resources, which can be any number of things:

- a university or federal HPC cluster with SLURM, PBS, or some other queue system
- a single node or even a Kubernetes cluster on a cloud provider
- a series of desktop computers that your lab shares
- any combination of these resources

The easiest way to use these resources is to sign on and run a simmate workflow using the `run` method. When this is done, the workflow runs directly on your resource. 

This was done in the "Run a workflow" tutorial when we called `simmate workflows run ...`. When on a HPC SLURM cluster, we would run simmate using a `submit.sh`:

```
#!/bin/bash

#SBATCH --output=slurm.out
#SBATCH --nodes=1
#SBATCH --ntasks=2

simmate workflows run-yaml my_settings.yaml > simmate.out
```

!!! tip 
    If you are only running a few workflows per day (<10), we recommend you stick to running workflows in this way. That is, just calling `simmate workflows run`. Don't overcomplicate things. Go back to tutorial 02 to review these concepts.

-------------------------------------------------------------------------------

## Deciding to set up workers

If your team is submitting hundreds or thousands of workflows at a time, then it would be extremely useful to monitor and orchestrate these workflows using a **scheduler** and **cluster**. 

Just like with our cloud database in the previous tutorial, you only need **ONE** person to manage **ALL** of your computational resources. Once the resources have been set up, the other users can connect using the database connection file (or an API key if you are using Prefect).

If you are that one person for your team, then continue with this tutorial. If not, then you should instead talk with your point person! Using your teams resources should be as easy as switching from the `run` to `run_cloud` method.

-------------------------------------------------------------------------------
