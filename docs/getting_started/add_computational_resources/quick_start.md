# Distributed Computational Resources

## Quick Start

1. If your computational resources are spread across different computers, ensure you've set up a cloud database (refer to the previous tutorial for guidance).
    
    !!! tip
        Remember, it's possible to share a cloud database **without** sharing computational resources. This flexibility is crucial for many collaborations. 

    !!! warning
        If you plan to schedule and run everything on your local computer (or file system), you can skip this step and use `sqlite` for now. *But*... SQLite can not handle parallelization - so you may see errors/crashes with highly parallel workloads.

2. For remote resources, ensure all simmate installations are connected to the same database (i.e., make sure `simmate config` matches accross computers).
``` bash
simmate config show --user-only
```
    
    !!! note
        If you are using a custom app (w. tables or workflows), ensure all resources have this app installed

3. Schedule your simmate workflows by switching from the `run` method to the `run-cloud` command. This workflow will be scheduled but won't run until a worker is started:
``` bash
simmate workflows run-cloud my_settings.yaml
```

4. Start a worker wherever you want to run the workflow with the following command. This "singleflow" worker will start, run one workflow, then shut down:
``` bash
simmate engine start-singleflow-worker
```

    !!! danger
        If you are on a cluster, `start-worker` should be called within your submit script (e.g., inside `submit.sh` for SLURM). Avoid running workers on the head node.

5. For more control over the number of workflows ran or to run a worker indefinitely, use the command:
``` bash
simmate engine start-worker
```

    !!! tip
        By default, any worker can pick up any workflow submission. To better control which workers run which workflows, use tags. Workers will only pick up submissions that have matching tags. See the Full Guides for more information.

6. Expand your cluster! Start workers wherever you want, and start as many as you need. Just ensure you follow steps 4 and 5 for every worker. If you need to start multiple workers simultaneously, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate engine start-cluster 5
```

    !!! tip
        For HPC clusters, you can also utilize commands such as `simmate engine start-cluster 5 --type slurm` 

7. To allow others to use your cluster, simply connect them to the same database.
