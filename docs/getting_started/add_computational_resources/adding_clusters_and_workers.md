
# Setting up your cluster and workers

-------------------------------------------------------------------------------

## Run vs. Run-cloud

Scheduling a workflow is straight-forward. Simply change all your scripts and commands from the `run` method to the `run_cloud` method. For example, if you are using the command line:

=== "command line"
    ``` bash
    simmate workflows run-cloud my_settings.yaml
    ```
=== "python"
    ``` python
    workflow.run_cloud(...)
    ```

This schedules your workflow, but it won't run yet. It is simply sitting in the queue and waiting for a worker to pick it up. Once we start a worker, then it will actually run.

-------------------------------------------------------------------------------

## Start a "single-flow" worker

Whereever you'd like to run the workflow, start a worker with:
``` bash
simmate workflow-engine start-singleflow-worker
```

!!! danger
    If you are on a cluster, start-worker should be called within your submit script (e.g. inside `submit.sh` for SLURM). Don't run workers on the head node! :warning: :warning: :warning: :warning: :warning: :warning:

-------------------------------------------------------------------------------

## Start a "many-flow" worker

When you run this "singleflow" worker, you'll notice that the Worker will start, run 1 workflow, then shutdown. This is the recommended approach for HPC clusters because it follow best practices for sharing resources. You don't want a worker hogging computational resources if there aren't any workflows scheduled to run! 

However, if you would like more control over how many workflows are ran or even run a worker endlessly, you can use the command:
``` bash
simmate workflow-engine start-worker
```

If your team runs many mini workflows that are under 5 minutes, starting/stopping workers could be a pain (sometimes it can take simmate up to 10 seconds to set everything up). That's a significant overhead and wasted computation time. 

To overcome this, we would run a worker that shuts down after 10 workflows or if the queue is empty:
``` bash
simmate workflow-engine start-worker --nitems-max 10 --close-on-empty-queue
```

-------------------------------------------------------------------------------

## Starting many workers at once

If you need to start many workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate workflow-engine start-cluster 5
```

-------------------------------------------------------------------------------

## Controlling what workflows are ran by each worker

!!! warning
    The full guide for custom workers is still being written. See workflow "tags" in the full guides for more information.

-------------------------------------------------------------------------------

## Connecting others to your scheduler

If they are connected to your database, then they're good to go! Other schedulers like Prefect or Dask require extra setup.

-------------------------------------------------------------------------------
