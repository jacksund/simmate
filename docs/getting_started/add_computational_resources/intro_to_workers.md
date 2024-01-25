# Introduction to Workers

-------------------------------------------------------------------------------

## When to Use Workers

If you're only executing a few workflows per day (<10), we recommend sticking to the `run` method for workflows. In other words, just execute `simmate workflows run` and avoid unnecessary complexity.

!!! example 

    Rather than mess with Simmate workers & cloud submissions, you can run workflows on an HPC SLURM cluster using a `submit.sh`:

    ```
    #!/bin/bash

    #SBATCH --output=slurm.out
    #SBATCH --nodes=1
    #SBATCH --ntasks=2

    simmate workflows run-yaml my_settings.yaml > simmate.out
    ```

On the other hand, if your team is submitting hundreds or thousands of workflows simultaneously, it would be highly beneficial to monitor and manage these workflows using Simmate workers.

-------------------------------------------------------------------------------

## What is a worker?

A worker is process that checks for scheduled workflow submissions and then runs them for you. In Simmate, workers run one workflow at a time -- pulling from your database, which stores a list of submitted jobs.

To see this in action...

1. Start a worker (and leave it running) with the command:
``` bash
simmate engine start-worker
```

2. You will notice that your worker is not actually doing anything yet. This is because we haven't submitted any jobs. Open a **new** terminal so that we can submit the workflow used in an earlier tutorial. Note how we are using `run-cloud` instead of `run`:
``` yaml
# in example.yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
```
``` bash
simmate workflows run-cloud example.yaml
```
    
    !!! warning
        Don't forget -- we need our `POSCAR` file in the same directory as where we are submitting. 

3. Once you submit your workflow, you should see your worker (which we left running) pick up the submission and run it.

This was **1 workflow submission** and **1 worker** -- both done on our laptop.

Howeer, in practice, you may submit hundreds of workflows from your local laptop and then start hundreds of workers on remote computers (such an HPC cluster). The workers would then pick up your jobs and run them in parallel!

!!! tip
    "1 computer = 1 worker" is not always the case. To prove this, you can open up multiple terminals and run the command `simmate engine start-worker` in each.

    Beware though -- the number of workers per computer should be based on the computer's CPU and Memory specs. If you start too many workers on a single computer, it may exceed the system limits and cause workers to crash.

-------------------------------------------------------------------------------

## Where do workers run?

Anywhere Simmate is installed! 

In the previous section we saw that we can start workers on our local laptop. In practice, most research teams manage their own computational resources, which could include:

- A university or federal HPC cluster with SLURM, PBS, or another queue system
- A series of nodes or a Kubernetes cluster on a cloud provider
- A collection of shared desktop computers within your lab
- Any combination of these resources

Simmate let's you distribute workers accross all of these. The only requirement is that each resource has access to your database (typically through a simple internet connection).

As real-world example, let's look at the Warren Lab at UNC. We have access to 3 different HPC clusters and submit workers to each. All of these workers are connected to the same database AND all users submit to the same database as well. This lets us distribute all calculations across the hundreds of compute nodes that we have access to: 

=== "General Setup"
    ``` mermaid
    graph TD;
        A[user 1]-->E[scheduler];
        B[user 2]-->E;
        C[user 3]-->E;
        D[user 4]-->E;
        E-->F[cluster 1];
        E-->G[cluster 2];
        E-->H[cluster 3];
        F-->I[worker 1];
        F-->J[worker 2];
        F-->K[worker 3];
        G-->L[worker 4];
        G-->M[worker 5];
        G-->N[worker 6];
        H-->O[worker 7];
        H-->P[worker 8];
        H-->Q[worker 9];
    ```
=== "Example (The Warren Lab)"
    ``` mermaid
    graph TD;
        A[Jack's submissions]-->E[cloud database];
        B[Scott's submissions]-->E;
        C[Lauren's submissions]-->E;
        D[Siona's submissions]-->E;
        E-->F[WarWulf];
        E-->G[LongLeaf];
        E-->H[DogWood];
        F-->I[slurm job 1];
        F-->J[slurm job 2];
        F-->K[slurm job 3];
        G-->L[slurm job 4];
        G-->M[slurm job 5];
        G-->N[slurm job 6];
        H-->O[slurm job 7];
        H-->P[slurm job 8];
        H-->Q[slurm job 9];
    ```

-------------------------------------------------------------------------------
