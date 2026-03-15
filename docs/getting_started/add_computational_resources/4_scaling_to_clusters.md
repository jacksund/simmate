# Parallel Clusters

Running one worker is great for background jobs, but what if you have a powerful machine with many cores? You probably want to run multiple jobs at once! 

This is where **Clusters** come in. In Simmate, a cluster is simply a collection of workers running at the same time.

---

## 1. Starting a Local Cluster

If you have a workstation with 8 cores, you might want to run 4 jobs in parallel (each using 2 cores). To do this, you can start a local cluster:

```bash
# Starts 4 workers on your local machine
simmate engine start-cluster 4 --type local
```

This command will open 4 separate background processes. Each process is its own worker, and each will pick up a job from the queue and run it.

---

## 2. Choosing the right number of workers

How many workers should you start? This depends on two things:

1. **How many cores do you have?** If you have 8 cores, you shouldn't start 20 workers. You'll slow down your entire computer!
2. **How many cores does each workflow need?** Some workflows (like VASP) can use many cores at once. If your workflow is set up to use 4 cores, and you start 4 workers, you'll need 16 cores total.

!!! tip "Start Small"
    If you're not sure, start with 2 or 3 workers and see how your computer handles the load. You can always stop the cluster (Ctrl+C) and restart it with a different number of workers.

---

## 3. Persistent Clusters

By default, `start-cluster` will start the requested number of workers and then finish. However, you can make the cluster "persistent" by using the `--continuous` flag:

```bash
# Keeps exactly 4 workers running at all times. 
# If one finishes and exits, a new one will automatically start!
simmate engine start-cluster 4 --type local --continuous
```

This is the most common way to run a cluster on a local workstation. It ensures your machine is always busy as long as there is work in the queue.

---

## Next Steps
Now that you can manage multiple workers on one machine, let's look at how to scale to **supercomputers** and **the cloud**.
