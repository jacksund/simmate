# Utilizing Computational Resources

## Quick Guide

1. Remember, it's possible to share a cloud database **without** sharing computational resources. This flexibility is crucial for many collaborations. 

2. As with your cloud database, assign a point-person to manage your private computational resources. All other users simply need to switch from `run` to `run_cloud`.

3. If your computational resources are spread across different computers, ensure you've set up a cloud database (refer to the previous tutorial for guidance). If you plan to schedule and run everything on your local computer (or file system), you can skip this step.

4. For remote resources, ensure all simmate installations are connected to the same database (i.e., your database connection file should be present on all resources).

5. If you're using custom workflows, ensure you're using a simmate project and all resources have this app installed. If you don't have custom database tables, you can try proceeding without this step, but registering via an app is the only way to ensure the workflow will run correctly.

6. Schedule your simmate workflows by switching from the `run` method to the `run_cloud` method. This workflow will be scheduled but won't run until a worker is started:
``` bash
simmate workflows run-cloud my_settings.yaml
```

7. Start a worker wherever you want to run the workflow with the following command. :warning::warning: If you're on a cluster, `start-worker` should be called within your submit script (e.g., inside `submit.sh` for SLURM). Avoid running workers on the head node.
``` bash
simmate engine start-singleflow-worker
```

8. This "singleflow" worker will start, run one workflow, then shut down. For more control over the number of workflows run or to run a worker indefinitely, use the command:
``` bash
simmate engine start-worker
```

9. Expand your cluster! Start workers wherever you want, and start as many as you need. Just ensure you follow steps 4 and 5 for every worker. If you need to start multiple workers simultaneously, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate engine start-cluster 5
```

10. To control which workers run which workflows, use tags. Workers will only pick up submissions that have matching tags.
``` bash
# when submitting
simmate workflows run-cloud ... -t my_tag -t small-job

# when starting the worker (typically on a different computer)
simmate engine start-worker -t small-job
```

11. To allow others to use your cluster, simply connect them to the same database.
