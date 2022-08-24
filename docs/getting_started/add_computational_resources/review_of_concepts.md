
# A review of concepts

Recall from tutorial 2, there are 4 steps to a workflow:
- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. calling VASP), and checks the results for errors
- `save`: saves the results to our database

This tutorial will give an overview of how to modify the `schedule` and determine which computer `execute` is called on. Up until now, we have been using the default behavior for these two steps. But now we want to instead do the following:
- `schedule`: submits the workflow to a scheduler queue of many other workflows
- `execute`: run the calculation on a remote cluster

A **scheduler** is something we submit workflows to and controls when to run them. The terms "scheduler" and "executor" are sometimes used interchangeably. As a bunch of workflows are submitted, our scheduler forms a queue and keeps track of which ones to run next. To do this, we can use the built-in `SimmateExecutor`, [Dask](https://docs.dask.org/en/stable/futures.html), or [Prefect](https://www.prefect.io/) as our scheduler. For this tutorial, we will use the `SimmateExecutor` because it is the default one and it's already set up for us.

A **cluster** is a group of computational resources that actually run the workflows. So our scheduler will find whichever workflow should be ran next, and send it to our cluster to run. Clusters are often made up of **workers** -- where a worker is just a single resource and it works through one job at a time. For example, say we have 10 computers (or slurm jobs) that each run one workflow at a time. All computers together are our cluster. Each computer is a worker. At any given time, 10 workflows will be running because each worker will have one it is in charge of. Because we are using the `SimmateExectuor`, we will be using `SimmateWorker`s to set up each worker and therefore our cluster. Set-up for each worker is the same -- whether your resources are on a cloud service, a supercomputer, or just simple desktops.
