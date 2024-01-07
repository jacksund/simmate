!!! danger
    This application is currently undergoing preliminary testing and is not intended for use outside of the Warren Lab.

!!! danger
    :warning::warning: **Ensure you are using a cloud database if your workers are operating on separate machines or an HPC cluster.** :warning::warning:
    
    The default database backend (sqlite) is not designed for parallel connections from different computers. Your calculations will be **slower** and **more prone to errors** with sqlite.
    
    If you encounter the error `database is locked`, it means you have exceeded the capabilities of sqlite.

!!! warning
    A functioning VASP installation is required, as with previous tutorials.

-------------------------------------------------------------------------------

## Quick Tutorial


### Fixed-Composition Search

1) Familiarize yourself with the input options and default settings of the `structure-prediction.toolkit.fixed-composition` workflow.
``` bash
simmate workflows explore
```

2) (Optional) If you wish to include prototype structures or known materials at the start of your search, ensure you have loaded the data into your cloud database. 
[This was discussed in a previous tutorial](http://127.0.0.1:8000/getting_started/use_a_cloud_database/build_a_postgres_database/#vii-load-third-party-data).

3) Create your input `yaml` file (e.g. `my_search.yaml`). Refer to the full example for best practices.
=== "Basic Input"
    ``` yaml
    workflow_name: structure-prediction.toolkit.fixed-composition
    composition: Ca8N4F8
    ```
=== "Best-Practice Input"
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

    1. The default input parameter `subworkflow: relaxation.vasp.staged` is used to analyze each structure. You can modify this workflow's behavior with the `subworkflow_kwargs` setting.
    2. This is the command each relaxation step will use.
    3. Since you probably won't be reviewing the output files of each calculation, and these results can consume a lot of disk space, this setting will convert completed calculations to `zip` files to save space.
    4. The status of individual structures and the writing of output files are checked in cycles. If your average relaxation takes 30 minutes, you don't need to check/update every 60 seconds (the default). Longer sleep steps help reduce database load.
    5. By default, `nsteadystate` is set to 40, meaning the search will maintain 40 total calculations in the queue at all times, regardless of the number of available workers. **The number of workers (not `nsteadystate`) controls the number of parallel calculations.** Only change this value if you want more than 40 calculations to run in parallel, which requires >40 running workers. Therefore, you can increase this value if needed, but **do NOT decrease `nsteadystate`**.

4) Submit the workflow settings file to start scheduling jobs.
``` shell
simmate workflows run my_search.yaml
```

5) Start workers by submitting the `start-worker` command to a cluster's queue (e.g., SLURM) or wherever you want jobs to run. Submit as many workers as the number of workflows you want to run in parallel:
=== "Basic Worker"
    ``` shell
    simmate engine start-worker
    ```
=== "Best-Practice Worker"
    ``` shell
    # (1)
    simmate engine start-worker --close-on-empty-queue --nitems-max 10
    ```
    
    1. `--close-on-empty-queue` shuts down the worker when the queue is empty, freeing up computational resources. `--nitems-max` limits the number of workflows each worker will run. Short-lived workers help maintain the health of a cluster and allow other SLURM jobs to cycle through the queue, preventing resource hogging.

6) Monitor the output and log files for any issues. Important error information can also be accessed via the command line:
``` bash
simmate engine stats
simmate engine error-summary
```

7) Submit new workers or cancel stale workers as needed.

### Binary-System Search

1. Follow the steps from the `fixed-composition` search above. The only differences here are the input yaml and follow-up searches. **Ensure you read and understand the best practices as well**.

2. Create your input yaml file:
``` yaml
workflow_name: structure-prediction.toolkit.chemical-system
chemical_system: Ca-N
```

3. Submit the search
``` bash
simmate workflows run my_search.yaml
```

4. Submit workers as needed
``` shell
simmate engine start-worker
```

-------------------------------------------------------------------------------