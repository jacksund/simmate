# Configuring Your Cluster and Workers

-------------------------------------------------------------------------------

## Switching from Run to Run-cloud

Transitioning a workflow to a schedule is simple. All you need to do is replace all your scripts and commands from the `run` method to the `run_cloud` method. For instance, if you're using the command line:

=== "command line"
    ``` bash
    simmate workflows run-cloud my_settings.yaml
    ```
=== "python"
    ``` python
    workflow.run_cloud(...)
    ```

This action schedules your workflow, but it doesn't initiate it. It merely places it in the queue, waiting for a worker to execute it. The workflow will only run once a worker is started.

-------------------------------------------------------------------------------

## Initiating a "single-flow" worker

To run the workflow, start a worker with the following command:
``` bash
simmate engine start-singleflow-worker
```

!!! danger
    If you're using a cluster, the start-worker command should be executed within your submit script (for example, inside `submit.sh` for SLURM). Avoid running workers on the head node! :warning: :warning: :warning: :warning: :warning: :warning:

-------------------------------------------------------------------------------

## Initiating a "many-flow" worker

When you initiate this "singleflow" worker, you'll observe that the Worker starts, executes one workflow, then shuts down. This method is recommended for HPC clusters as it adheres to best practices for resource sharing. It prevents a worker from monopolizing computational resources when there are no scheduled workflows to run! 

However, if you want more control over the number of workflows run or even to run a worker indefinitely, use the following command:
``` bash
simmate engine start-worker
```

If your team frequently runs many short workflows that take less than 5 minutes, constantly starting and stopping workers can be inconvenient (sometimes it can take simmate up to 10 seconds to set everything up). This can lead to significant overhead and wasted computation time. 

To mitigate this, you can run a worker that shuts down after executing 10 workflows or when the queue is empty:
``` bash
simmate engine start-worker --nitems-max 10 --close-on-empty-queue
```

-------------------------------------------------------------------------------

## Initiating Multiple Workers Simultaneously

If you need to initiate multiple workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate engine start-cluster 5
```

-------------------------------------------------------------------------------

## Managing the Workflows Run by Each Worker

!!! warning
    The comprehensive guide for custom workers is currently under development. Refer to the workflow "tags" in the full guides for more details.

-------------------------------------------------------------------------------

## Allowing Others to Connect to Your Scheduler

If others are connected to your database, they're all set! Other schedulers like Prefect or Dask may require additional setup.

-------------------------------------------------------------------------------