# Add computational resources

In this tutorial, you will learn how to run workflows on distributed computational resources -- with full scheduling and monitoring.


## The quick tutorial

!!! note
    This tutorial will use the default scheduler/executor, "SimmateExecutor". However, you can also use Prefect and/or Dask to build out your cluster. This is covered elsewhere, but it is not recommended at the moment.

1. Be aware that you can share a cloud database *without* sharing computational resources. This flexibility is very important for many collaborations. 

2. Just like with your cloud database, designate a point-person to manage your private computational resources. Everyone else only needs to switch from `run` to `run_cloud`.

3. If your computational resources are distributed on different computers, make sure you have set up a cloud database (see the previous tutorial on how to do this). If you want to schedule AND run things entirely on your local computer (or file system), then you can skip this step.

4. If you have remote resources, make sure you have ALL simmate installations connected to the same database (i.e. your database connection file should be on all resources).

5. If you have custom workflows, make sure you are using a simmate project and all resources have this app installed. However, if you don't have custom database tables, you can try continuing without this step -- but registering via an app is the only way to guarantee that the workflow will run properly.

6. Schedule your simmate workflows by switching from the `run` method to the `run_cloud` method. This workflow will be scheduled but it won't run until we start a worker:
``` bash
simmate workflows run-cloud relaxation.vasp.mit --structure POSCAR
```

8. Wherever you'd like to run the workflow, start a worker with the following command. :warning::warning: If you are on a cluster, start-worker should be called within your submit script (e.g. inside `submit.sh` for SLURM). Don't run workers on the head node.
``` bash
simmate workflow-engine start-singleflow-worker
```

9. Note this "singleflow" worker will start, run 1 workflow, then shutdown. If you would like more control over how many workflows are ran or even run a worker endlessly, you can use the command:
``` bash
simmate workflow-engine start-worker
```

10. Scale out your cluster! Start workers anywhere you'd like, and start as many as you'd like. Just make sure you follow steps 4 and 5 for every worker. If you need to start many workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate workflow-engine start-cluster 5
```

11. To control which workers run which workflows, use tags. Workers will only pick up submissions that have matching tags.
``` bash
# when submitting
simmate workflows run-cloud ... -t my_tag -t small-job

# when starting the worker (typically on a different computer)
simmate workflow-engine start-worker -t small-job
```

12. To let others use your cluster, simply connect them to the same database.

