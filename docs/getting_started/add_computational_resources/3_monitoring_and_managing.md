# Monitoring and Managing Jobs

Once you've submitted a few dozen (or hundred) jobs, you'll want to see how they're doing. Simmate gives you several tools for this, both from the command line and in Python.

---

## 1. CLI Monitoring

The `simmate engine` command group includes several tools to help you see what's happening in your queue:

### `stats`
This gives you a quick overview of how many jobs are in each state (Pending, Running, Finished, etc.):
```bash
simmate engine stats
```

### `workitems`
This shows a detailed table of every job in the queue, including its name, status, and tags:
```bash
simmate engine workitems
```

### `delete-finished`
If your queue gets too cluttered with finished jobs, you can clean them up:
```bash
simmate engine delete-finished
```

---

## 2. Python Monitoring

If you're writing a script, you'll want to check on your jobs programmatically.

When you submit a job with `.run_cloud()`, it returns a **WorkItem** object. This object acts as a "future"—a placeholder for the result that hasn't been computed yet.

```python
from simmate.workflows.static_energy.vasp.matproj import workflow

# Submit the job
workitem = workflow.run_cloud(structure="NaCl.cif")

# Check if it's done (non-blocking)
if workitem.is_done():
    print("Job is complete!")

# Get the status
print(f"Current status: {workitem.status}")

# Get the final result
# NOTE: This call is BLOCKING! It will wait for the job to finish.
result = workitem.result()
print(f"Final Energy: {result.energy}")
```

### Why use `result()`?
If you submit 100 jobs and want to wait for all of them to finish before continuing, you can do something like this:

```python
workitems = [workflow.run_cloud(structure=s) for s in structures]

# Wait for all jobs to finish and collect results
results = [wi.result() for wi in workitems]
```

---

## 3. The Web Interface

If you have the Simmate website running, you can monitor your jobs visually! 

Go to the **Workflows** page of your local website, and you'll see a live dashboard showing the status of your queue. It's much easier to see failures or long-running jobs this way.

---

## Next Steps
Now that you can manage a single worker, let's learn how to scale up to a **cluster** of workers to run jobs in parallel.
