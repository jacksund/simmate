
# Setting up your cluster and workers

After you go through the check-list above, you're ready to start a worker!

Scheduling a workflow is straight-forward. Simply change all your scripts and commands from the `run` method to the `run_cloud` method. For example, if you are using the command line:
``` bash
simmate workflows run-cloud relaxation.vasp.mit --structure POSCAR
```

This schedules your workflow, but it won't run yet. It is simply sitting in the queue and waiting for a worker to pick it up. Once we start a worker, then it will actually run.

Whereever you'd like to run the workflow, start a worker with:
``` bash
simmate workflow-engine start-singleflow-worker
```
> :warning::warning::warning: If you are on a cluster, start-worker should be called within your submit script (e.g. inside `submit.sh` for SLURM). Don't run workers on the head node! :warning::warning::warning:

When you run this "singleflow" worker, you'll notice that the Worker will start, run 1 workflow, then shutdown. This is the recommended approach for HPC clusters because it follow best practices for sharing resources. You don't want a worker hogging computational resources if there aren't any workflows scheduled to run! 

However, if you would like more control over how many workflows are ran or even run a worker endlessly, you can use the command:
``` bash
simmate workflow-engine start-worker
```

For example, if your team runs many mini workflows that are under 5 minutes, starting/stopping workers could be a pain (sometimes it can take simmate up to 10 seconds to set everything up). That's a significant overhead and wasted computation time. To overcome this, we would run a worker that shuts down after 10 workflows or if the queue is empty:
``` bash
simmate workflow-engine start-worker --nitems_max 10 --close_on_empty_queue true
```

If you need to start many workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate workflow-engine start-cluster 5
```

# Controlling what workflows are ran by each worker
> :warning: The full guide for custom workers is still being written. See workflow "tags" for more information.


# Connecting others to your scheduler

If they are connected to your database, then they're good to go! Other schedulers like Prefect or Dask require extra setup.


# You did it!

:fire::fire::fire::fire::fire::fire:

If you made it to this point, you're pretty much a Simmate expert! 

Any other guides and tutorials will be in the API documentation. We hope you see the potential Simmate has to offer the larger materials community! With a powerful framework like Simmate in hand, anything is possible. In other words...

**"The ceiling is the roof" -Michael Jordan**

Have fun coding and always be sure to ask for help/feedback when you need it.

:fire::fire::fire::fire::fire::fire:
