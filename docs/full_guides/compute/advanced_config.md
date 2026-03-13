# Advanced Configuration

You can fine-tune how workers behave and how jobs are distributed using several advanced options.

## Tags

Tags are the primary way to control which workers run which jobs. This is useful when you have heterogeneous hardware (e.g., some nodes with GPUs, some with high RAM).

### Submitting with Tags
In Python:
```python
workflow.run_cloud(..., tags=["high-ram", "project-x"])
```
In CLI:
```bash
simmate workflows run-cloud ... --tag high-ram --tag project-x
```

### Starting Workers with Tags
A worker will only pick up jobs that match **all** of its tags.
```bash
# This worker will only pick up jobs tagged with "high-ram"
simmate engine start-worker --tag high-ram
```

!!! note
    The `simmate engine start-cluster` command does not currently support passing custom tags to the workers it launches. Workers started this way will use the default `simmate` tag.

!!! warning
    **SQLite3 Tag Limitation:** If you are using the default SQLite3 database, all tags must be **exactly 7 characters long** and **all lowercase** (e.g., `simmate`, `default`, `custom1`). This is because SQLite does not support advanced JSON filtering, so Simmate uses basic substring matching. Forcing all tags to be the same length prevents a shorter tag (like `vasp`) from accidentally matching a longer one (like `vasp-relax`). If you need more flexible tagging, we highly recommend switching to a **Postgres** database.

---

## Timeouts & Limits

To prevent workers from running indefinitely or consuming too many resources, you can set limits.

### Time Limits
The worker will stop checking for new jobs after the timeout is reached. It will finish its current job before exiting.
```bash
# Shut down after 12 hours (43200 seconds)
simmate engine start-worker --timeout 43200
```

### Item Limits
The worker will shut down after completing a certain number of jobs.
```bash
# Shut down after running 5 jobs
simmate engine start-worker --nitems-max 5
```

---

## Startup Methods

Sometimes you need to perform custom setup on a worker before it starts pulling jobs (e.g., warming up a cache, setting environment variables that can't be set in a shell script).

You can provide a python path to a function that should be executed upon worker startup.

```bash
simmate engine start-worker --startup-method my_app.utils.worker_init
```

---

## Wait Times

By default, when the queue is empty, a worker waits 1 second before checking again. You can increase this to reduce database load if you have thousands of workers.

```bash
# Wait 60 seconds between queue checks
simmate engine start-worker --waittime-on-empty-queue 60
```

---

## Running in the Background

On most Linux systems, you can run a worker in the background using `nohup` or a terminal multiplexer like `tmux` or `screen`.

### Using `nohup`
```bash
nohup simmate engine start-worker > worker.log 2>&1 &
```
This will start the worker, redirect all output to `worker.log`, and keep it running even if you log out.

### Using `tmux`

1. Start a new session: `tmux new -s simmate-worker`
2. Run the worker: `simmate engine start-worker`
3. Detach: Press `Ctrl+B` then `D`
4. Re-attach later: `tmux attach -t simmate-worker`
