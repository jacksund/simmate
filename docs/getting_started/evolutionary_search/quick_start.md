
In this tutorial, you will learn how to submit an evolutionary search and other massively parallel workflows.

!!! danger
    :warning::warning: **Make sure you are using a cloud database if your workers are on separate 
    machines or an HPC cluster.** :warning::warning:
    
    The default database backend (sqlite) is not built for parallel connections 
    from different computers. Your calculations will be **slower** and
    **error-prone** with sqlite.
    
    If you are seeing the error `database is locked`, then you have 
    exceeded the capabilities of sqlite.

!!! warning
    Just like with earlier tutorials, a working VASP installation is required.

-------------------------------------------------------------------------------

## The quick tutorial


### A fixed-composition search

1) View input options and default settings of the `structure-prediction.toolkit.fixed-composition` workflow
``` bash
simmate workflows explore
```

2) (optional) If you wish for prototype structures or known materials to be included at the
start of your search, make sure you have loaded the data into your cloud database. 
[This was covered in an earlier tutorial](http://127.0.0.1:8000/getting_started/use_a_cloud_database/build_a_postgres_database/#vii-load-third-party-data).

3) Build our input `yaml` file (e.g. `my_search.yaml`). Be sure to look at the full example for best-practices.
=== "basic input"
    ``` yaml
    workflow_name: structure-prediction.toolkit.fixed-composition
    composition: Ca8N4F8
    ```
=== "best-practice input"
    ``` yaml
    workflow_name: structure-prediction.toolkit.fixed-composition
    composition: Ca8N4F8
    
    subworkflow_kwargs:  # (1)
        command: mpirun -n 8 vasp_std > vasp.out  # (2)
        compress_output: true  # (3)
        # see 'simmate workflows explore' on `relaxation.vasp.staged`
        # for other optional subworkflow_kwargs
    
    sleep_step: 300  # (4)
    nsteadystate: 100  # (5)
    
    # see 'simmate workflows explore' output for other optional inputs
    ```

    1. One of the default input parameters is `subworkflow: relaxation.vasp.staged`, which is used to analyze each structure. We can modify how this workflow behaves with the `subworkflow_kwargs` setting.
    2. The command that each relaxation step will be called with.
    3. You likely won't be reading through the output files of each calculation, and these resuklts will take up a lot of file space. This setting will convert completed calculations to `zip` files and help save on disk space.
    4. The status of individual structures & the writing of output files is checked on a cycle. If you know your average relaxation will take 30 minutes, then you likely don't need to check/update every 60 seconds (the default). Longer sleep steps help reduce database load.
    5. By default, `nsteadystate` is set to 40, which means the search will 
    maintain 40 total calculations in the queue at all times -- regardless of 
    the number of workers available. **The number of workers (not `nsteadystate`) 
    controls the number of parallel calculations.** This value should only be changed 
    if you want more than 40 calculations ran in parallel. This means >40 workers must be 
    running. Therefore, increase this value if you desire but **do NOT decrease
    `nsteadystate`**.

4) Submit the workflow settings file, which will start scheduling jobs.
``` shell
simmate workflows run my_search.yaml
```

5) Start workers by submitting the `start-worker` command to a cluster's queue (e.g. SLURM) or whereever you'd like jobs to run. Submit as many workers as workflows that you want ran in parallel:
=== "basic worker"
    ``` shell
    simmate engine start-worker
    ```
=== "best-pracitce worker"
    ``` shell
    # (1)
    simmate engine start-worker --close-on-empty-queue --nitems-max 10
    ```
    
    1. `--close-on-empty-queue` shuts down the worker when the queue is empty. This
    helps release computational resources for others. `--nitems-max` limits the number
    of workflows each worker will run. Short-lived workers help maintain the health
    of a cluster and also allow other SLURM jobs to cycle through the queue -- avoiding
    the hogging of resources.

6) Monitor the output and log files for any issues. Important error information
can also be accessed in the command line:
``` bash
simmate engine show-stats
simmate engine show-error-summary
```

7) Submit new workers or cancel stale workers as needed.

### A binary-system search

1. Follow the steps from the `fixed-composition` search above. The only difference
here will be (i) the input yaml and (ii) follow-up searches. **Make sure you read
and understand best practices as well**.

2. Build your input yaml file:
``` yaml
workflow_name: structure-prediction.toolkit.binary-system
chemical_sysyem: Ca-N
```

3. Submit the search
``` bash
simmate workflows run my_search.yaml
```

4. Submit workers as-needed
``` shell
simmate engine start-worker
```

-------------------------------------------------------------------------------
