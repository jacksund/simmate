# Basic Use

Simmate is designed to scale from a single laptop to large high-performance computing (HPC) clusters and cloud environments. It uses a **database-backed queue** system to manage and distribute tasks across any number of computers.

## Core Concepts

The system is built around three main components: **WorkItems**, **Executors**, and **Workers**.

### 1. WorkItems (The Queue)
Every time you submit a workflow for "cloud" execution, Simmate creates a **WorkItem** in your database. This entry contains everything needed to run the task:

- The function to be executed (serialized using `cloudpickle`).
- The input arguments and keyword arguments.
- Metadata like `status` (Pending, Running, Finished, etc.) and `tags`.


The database acts as the single source of truth and the communication bridge between different computers.

### 2. SimmateExecutor (The Submitter)
The `SimmateExecutor` is the component that puts jobs *into* the queue. When you call a workflow's `run_cloud()` method or use the `workflows run-cloud` CLI command, you are using an executor to create a `WorkItem` entry in the database.

The executor itself doesn't run the job; it just "schedules" it.

### 3. SimmateWorker (The Runner)
A `SimmateWorker` is a process that sits on a compute resource and waits for work. It follows a simple loop:

1. Poll the database for any `Pending` WorkItems.
2. If it finds one (and it matches its `tags`), it marks it as `Running`.
3. It downloads the task, executes it, and captures the result.
4. It saves the result back to the database and marks the WorkItem as `Finished` or `Errored`.

---

## Why this Architecture?

Most workflow engines (like Dask or Prefect) require a persistent network connection between a central scheduler and its workers. This often fails in scientific environments because:

- **Firewalls:** University and national lab clusters often block incoming connections to compute nodes.
- **Heterogeneous Resources:** You might want to run some jobs on your local machine, some on a SLURM cluster, and some on Google Cloud simultaneously.

Simmate's database-backed queue only requires workers to have **outbound** access to the database. This allows workers to be scattered across any number of clusters and firewalls, as long as they can all "see" the same database.

---

## Submitting Jobs

There are two ways to submit a workflow to the queue: via Python or the Command Line Interface (CLI).

### In Python
Instead of using the standard `.run()` method, use `.run_cloud()`. This method returns a `WorkItem` object immediately, which acts as a "future" (a placeholder for the result).

```python
from simmate.workflows.static_energy.vasp.matproj import workflow

# Submit the job to the queue
workitem = workflow.run_cloud(
    structure="NaCl.cif",
    command="vasp_std",
    tags=["my-tag"], # optional: defaults to ["simmate"]
)

# You can check if it's done without blocking
if workitem.is_done():
    print("Job is complete!")

# You can also check for other states
if workitem.is_running():
    print("Job is currently being worked on by a worker.")
elif workitem.is_pending():
    print("Job is still waiting in the queue.")

# To get the result, call .result(). 
# NOTE: This call is BLOCKING, meaning it will wait for the job to complete 
# before returning the result (or raising an error if the job failed).
result = workitem.result()
```

If you need to stop a job that is still `Pending`, you can use `workitem.cancel()`. Jobs that are already `Running` or `Finished` cannot be canceled.

### From the CLI
Use the `run-cloud` command followed by your workflow name and inputs (either as arguments or a YAML file).

```bash
simmate workflows run-cloud static-energy.vasp.matproj --structure NaCl.cif
```

---

## Starting Workers

Once jobs are submitted, they stay in the `Pending` state until a worker picks them up. You can start a worker on any machine where Simmate is installed and configured.

### Starting a Persistent Worker
A persistent worker will stay alive and continue to check for new jobs indefinitely.

```bash
simmate engine start-worker
```

### Starting a Single-Flow Worker
A "single-flow" worker will pull **one** job from the queue, execute it, and then shut down. If the queue is empty, it shuts down immediately. This is highly recommended for HPC clusters where you submit many individual jobs to a scheduler like SLURM.

```bash
simmate engine start-singleflow-worker
```

This is equivalent to:
```bash
simmate engine start-worker --nitems-max 1 --close-on-empty-queue
```

### Starting a Local Cluster
If you are on a powerful workstation and want to start multiple workers at once, use the `start-cluster` command.

```bash
# Starts 4 workers on your local machine
simmate engine start-cluster 4 --type local
```

---

## Configuration Checklist

For distributed execution to work correctly, ensure:

1. **Shared Database:** All submitters and workers must be connected to the same database. Check your config with:
   ```bash
   simmate config show
   ```
2. **Software Availability:** The worker must have the necessary software installed to run the workflow (e.g., `vasp_std` must be in the PATH if you are running VASP workflows).
3. **App Registration:** If you are using custom apps or workflows, the worker must have those apps installed and registered in its `settings.yaml`.
