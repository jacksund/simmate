
# Intro to engine concepts

-------------------------------------------------------------------------------

## Overview

Recall from our earlier tutorial, there are 4 steps to a workflow (`configure`, `schedule`, `execute`, and `save`).

This tutorial will give an overview of how to modify the `schedule` and determine which computer `execute` is called on. Up until now, we have been using the default behavior for these two steps. But now we want to instead do the following:

- `schedule`: submit the workflow to a queue of many other workflows
- `execute`: run the calculation on a remote cluster

-------------------------------------------------------------------------------

## Visualizing our setup

The following schematic will help with understanding the concepts described below. Take a moment to understand the organization our resources and use this as a reference when reading below.

=== "general setup"
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
=== "example (the Warren lab)"
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

## What is a scheduler?

A **scheduler** is something we submit workflows to and it is what controls when & where to run workflows. 

The terms "scheduler" and "executor" are sometimes used interchangeably. As a bunch of workflows are submitted, our scheduler forms a queue and keeps track of which ones to run next. To do this, we can use the built-in `SimmateExecutor`, [Dask](https://docs.dask.org/en/stable/futures.html), or [Prefect](https://www.prefect.io/) as our scheduler. For this tutorial, we will use the `SimmateExecutor` because it is the default one and it's already set up for us.

-------------------------------------------------------------------------------

## What is a cluster?

A **cluster** is a group of computational resources that actually run the workflows. So our scheduler will find whichever workflow should be ran next, and send it to our cluster to run. 

Clusters are often made up of **workers** -- where a worker is just a single resource and it works through one job at a time. For example, say we have 10 computers (or slurm jobs) that each run one workflow at a time. All computers together are our cluster. Each computer is a worker. At any given time, 10 workflows will be running because each worker will have one it is in charge of. Because we are using the `SimmateExectuor`, we will be using `SimmateWorker`s to set up each worker and therefore our cluster. Set-up for each worker is the same -- whether your resources are on a cloud service, a supercomputer, or just simple desktops.

-------------------------------------------------------------------------------
