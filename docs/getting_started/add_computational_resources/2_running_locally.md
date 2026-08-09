# Running Locally

To use workers, you need a database that can handle multiple connections at once. In the previous tutorial, we set up **Postgres**. This is the key that makes workers possible!

In this tutorial, we'll start a worker on your computer and submit a job for it to process.

---

## 1. Start a Worker

Open a terminal and run the following command. This starts a worker that will stay "on duty" until you stop it (with `Ctrl+C`).

```bash
simmate compute start-worker
```

Your worker is now polling the database: *"Any jobs? (... wait a little ...) Any jobs now?"* Since the queue is empty, it will just continue to wait.

---

## 2. Submit a "Cloud" Job

Open a **new** terminal. We're going to submit a workflow to the queue rather than running it immediately.

Instead of using the standard `run` command, we use `run-cloud`. This command tells Simmate to "pin the order to the board" rather than cooking it ourselves.

First, save your workflow settings to a file:
```yaml
# save this as example.yaml
workflow_name: relaxation.vasp.quality00
structure: NaCl.cif
```

Then, submit the job to your queue:
```bash
simmate workflows run-cloud example.yaml
```

After running this command, Simmate will tell you the **workitem_id** of your job. You can immediately continue using your terminal for other things!

---

## 3. Watch the Magic

Switch back to your **first terminal** (where the worker is running). You'll see the worker pick up the job and start running it!

```text
=====================================================================
   _____                  __        _      __         __
  / __(_)_ _  __ _  ___ _/ /____   | | /| / /__  ____/ /_____ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_)  | |/ |/ / _ \/ __/  '_/ -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/   |__/|__/\___/_/ /_/\_\\__/_/

=====================================================================

2026-03-15 12:50:57 INFO     Starting worker with tags ['simmate']
2026-03-15 12:50:57 INFO     Worker is ready & listening for WorkItems
2026-03-15 12:51:00 INFO     Running WorkItem with id 1
... workflow output ...
2026-03-15 12:51:10 INFO     Completed WorkItem
```

---

## What happened?

1. The `run-cloud` command created a **WorkItem** in your database with a status of `Pending`.
2. The **Worker** saw the `Pending` job, changed its status to `Running`, and executed the workflow.
3. When finished, the **Worker** updated the status to `Finished` (or `Completed`) and saved the results.

This simple workflow is the foundation for everything you'll do with Simmate. Whether you're running 1 job on your laptop or 10,000 jobs on a supercomputer, the process is the same.

---

## Next Steps
Now that you know how to run a worker, let's learn how to monitor your jobs and see their results.
