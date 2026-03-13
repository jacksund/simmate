# HPC & SLURM Clusters

Simmate is frequently used on High-Performance Computing (HPC) clusters that use the SLURM workload manager.

## Connecting to the Database

HPC compute nodes must be able to connect to your central Simmate database. 

- **Internal Databases:** Some universities provide database hosting within their network.
- **Cloud Databases:** You can use a managed Postgres service (e.g., DigitalOcean, AWS) if your cluster allows outbound connections to the internet.

Always verify the connection from a compute node (not just the login node) before starting a large number of workers.

---

## Submitting Workers via SLURM

The most common way to run Simmate on a cluster is to submit "single-flow" workers. This allows SLURM to manage the allocation of resources for each individual workflow run.

### Manual Submission (`sbatch`)
You can create a standard SLURM `submit.sh` script that launches a Simmate worker:

```bash
#!/bin/bash
#SBATCH --job-name=simmate-worker
#SBATCH --output=slurm-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=24:00:00

# Load any necessary modules (e.g. for VASP)
module load vasp

# Start a worker that runs one job and then exits.
# NOTE: This uses the default tag 'simmate'.
simmate engine start-singleflow-worker

# To use custom tags, use the full start-worker flags:
# simmate engine start-worker --tag my-tag --nitems-max 1 --close-on-empty-queue
```

Submit this script multiple times to start multiple workers:
```bash
sbatch submit.sh
```

### Automatic Submission (`start-cluster`)
Simmate provides a convenience command to submit many workers to SLURM at once.

```bash
# Submits 100 workers to SLURM
simmate engine start-cluster 100 --type slurm
```

!!! note
    This command expects a file named `submit.sh` to exist in your current directory. It will use `sbatch submit.sh` to submit each worker. Ensure your `submit.sh` has the correct `sbatch` headers for your cluster.

---

## Common HPC Issues

### Command Not Found
If a workflow fails with a `CommandNotFoundError`, it usually means the worker couldn't find the external program (like `vasp_std` or `pw.x`). 

**Solution:** Ensure your `submit.sh` script properly sets up the environment (e.g., `module load`, `export PATH`, or `conda activate`).

### Firewall/Network Issues
If your worker starts but cannot connect to the database, it will likely hang or crash.

**Solution:** Test the connection with `simmate database wait-for-db` or a simple `psql` command from a compute node to ensure the port (typically 5432) is open.

### SQLite in HPC
**Never use the default SQLite database for distributed HPC execution.** SQLite does not support multiple concurrent writes from different nodes and will result in "Database is locked" errors and data corruption. Always use **Postgres** for multi-node setups.
