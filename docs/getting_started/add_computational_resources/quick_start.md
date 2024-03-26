# Distributed Computational Resources

## Quick Start

!!! tip
    While this section is intended for distributing workflows accross many computers, you can stick to your local laptop for this Quick Start and learning the basics.

!!! warning
    If you are running everything on your local computer, you can use the default database (`sqlite`) for now. *HOWEVER*... SQLite can not handle parallelization - so you may see errors/crashes with highly parallel workloads. Limit the number of workers you start.

    If your computational resources are distributed across different computers, ensure you've set up a cloud database, such as a Postgres database on DigitalOcean. Further, all workers need access to your database in order to function.


1. For remote resources, ensure all simmate installations are connected to the same database. In other words, make sure the `config` matches accross computers. This step is unnecessary if you are on a single computer.
``` bash
simmate config show --user-only
```
    
    !!! note
        If you are using a custom app (w. tables or workflows), ensure all resources have this app installed

1. Create your workflow settings as you normally do. Here we will use a `YAML` file, but you can use Python or the CLI as well:
``` yaml
# in example.yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
```

1. Schedule your simmate workflows by switching from the `run` to the `run-cloud` command (in python use the `run_cloud()` method instead of `run()`). This workflow will be scheduled but won't run until a worker is started:
``` bash
simmate workflows run-cloud example.yaml
```

1. Start a worker wherever you want to run the workflow with the following command. This "singleflow" worker will start, run one workflow, then shut down:
``` bash
simmate engine start-singleflow-worker
```

    !!! danger
        If you are on a cluster, `start-worker` should be called within your submit script (e.g., inside `submit.sh` for SLURM). Avoid running workers on the head node.

1. For more control over the number of workflows ran or to run a worker indefinitely, use the command:
``` bash
simmate engine start-worker
```

    !!! tip
        By default, any worker can pick up any workflow submission. To better control which workers run which workflows, use tags. Workers will only pick up submissions that have matching tags. See the Full Guides for more information.

1. Expand your cluster! Start workers wherever you want, and start as many as you need. Just ensure you follow steps 4 and 5 for every worker. If you need to start multiple workers simultaneously, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate engine start-cluster 5
```

    !!! tip
        For HPC clusters, you can also utilize commands such as `simmate engine start-cluster 5 --type slurm` 

1. To allow others to use your cluster, simply connect them to the same database.
