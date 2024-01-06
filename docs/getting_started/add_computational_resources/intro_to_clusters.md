# Introduction to Engine Concepts

-------------------------------------------------------------------------------

## Overview

In a previous tutorial, we discussed the four steps of a workflow: `configure`, `schedule`, `execute`, and `save`.

This tutorial will focus on how to modify the `schedule` and determine the computer on which `execute` is called. Until now, we have been using the default behavior for these two steps. However, we will now explore how to:

- `schedule`: Submit the workflow to a queue containing multiple workflows.
- `execute`: Run the calculation on a remote cluster.

-------------------------------------------------------------------------------

## Visualizing Our Setup

The schematic below will aid in understanding the concepts discussed in this tutorial. Take a moment to familiarize yourself with the organization of our resources and refer back to this schematic as needed.

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

## What is a Scheduler?

A **scheduler** is a tool to which we submit workflows. It controls when and where workflows are run. 

The terms "scheduler" and "executor" are often used interchangeably. As workflows are submitted, the scheduler forms a queue and determines the order of execution. We can use the built-in `SimmateExecutor`, [Dask](https://docs.dask.org/en/stable/futures.html), or [Prefect](https://www.prefect.io/) as our scheduler. For this tutorial, we will use the `SimmateExecutor` as it is the default option and is already set up for us.

-------------------------------------------------------------------------------

## What is a Cluster?

A **cluster** is a collection of computational resources that execute the workflows. The scheduler identifies the next workflow to be run and sends it to the cluster for execution. 

Clusters typically consist of **workers** -- individual resources that process one job at a time. For instance, if we have 10 computers (or slurm jobs) each running one workflow at a time, these computers collectively form our cluster. Each computer is a worker. At any given time, 10 workflows will be running, with each worker handling one. As we are using the `SimmateExectuor`, we will use `SimmateWorker`s to set up each worker and, consequently, our cluster. The setup for each worker is the same, regardless of whether your resources are on a cloud service, a supercomputer, or simple desktops.

-------------------------------------------------------------------------------