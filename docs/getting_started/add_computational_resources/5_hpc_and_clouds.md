# HPC & Clouds

Running workers on your local computer is a great start, but true high-throughput research requires scaling out to **HPC supercomputers** and **the cloud**. 

Since Simmate uses a database as the central queue, you can start workers on any machine that has an internet connection and the right software installed.

---

## 1. HPC Supercomputers (SLURM)

Most supercomputers use a scheduler called **SLURM** to manage jobs. Simmate has built-in support for submitting workers directly to SLURM.

To start 100 workers on a supercomputer:
```bash
# Submits 100 workers to the SLURM queue
simmate compute start-cluster 100 --type slurm
```

### The `submit.sh` Template
To use the `slurm` type, you need a `submit.sh` file in your current directory. This file is your "recipe" for how to run a job on your cluster. Simmate will take this file and automatically swap out the command at the end for `simmate compute start-worker`.

Here's a simple `submit.sh` example:
```bash
#!/bin/bash
#SBATCH --job-name=simmate_worker
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=general
#SBATCH --time=24:00:00

# (Any other setup you need, like module loads)
module load vasp

# Simmate will add "simmate compute start-worker" here
```

---

## 2. Cloud Resources (Kubernetes)

If you're using a cloud provider like Google Cloud or AWS, you'll likely use **Kubernetes**. Simmate is designed to run in a Kubernetes environment. 

We provide **Helm charts** and **Dockerfiles** to help you deploy a cluster of workers that automatically scales based on the size of your queue.

---

## 3. Shared Resources (The Warren Lab)

The real power of Simmate comes when you have a whole team of researchers all submitting jobs to the same database.

``` mermaid
graph TD;
    A[Jack's submissions]-->E[Cloud Database];
    B[Scott's submissions]-->E;
    C[Lauren's submissions]-->E;
    D[Siona's submissions]-->E;
    E-->F[Cluster 1: Local Workstation];
    E-->G[Cluster 2: HPC Cluster];
    E-->H[Cluster 3: Cloud Nodes];
    F-->I[Worker 1];
    G-->J[Worker 2];
    G-->K[Worker 3];
    H-->L[Worker 4];
```

By connecting everyone to the same database, your entire team can share a single "pool" of computational power. You can even check each other's results directly in the database!

---

## Where to go next?

This concludes our tour of computational resources! You now have a solid understanding of how Simmate manages background tasks.

For more technical details and advanced configurations, check out the **Full Guides**:

- [HPC & SLURM Setup](../../full_guides/compute/hpc_slurm.md)
- [Cloud & Kubernetes Setup](../../full_guides/compute/cloud_kubernetes.md)
- [Advanced Monitoring](../../full_guides/compute/monitoring_and_cleanup.md)
