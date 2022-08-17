# -*- coding: utf-8 -*-

import logging
import subprocess
from pathlib import Path
from tempfile import mkdtemp


def start_cluster(
    nworkers: int,
    worker_command: str = "simmate workflow-engine start-worker",
):

    cluster_directory = mkdtemp(prefix="simmate-cluster-", dir=Path.cwd())

    logging.info(f"Starting up cluster in {cluster_directory}")

    # For as many workers that were requested, go through and start that many
    # subprocesses for individual workers.
    all_popens = []
    for n in range(nworkers):

        output_file = Path.cwd() / cluster_directory / f"worker_{n}.out"

        popen = subprocess.Popen(
            worker_command,
            shell=True,
            stdout=output_file.open("w"),
            stderr=output_file.open("w"),
        )
        all_popens.append(popen)

    logging.info(f"A total of {nworkers} workers have been started.")
    logging.info("Waiting until all workers workers shut down...")

    # Now just wait for the process to finish. Note we use communicate
    # instead of the .wait() method. This is the recommended method
    # when we have stderr=subprocess.PIPE, which we use above.
    [popen.communicate() for popen in all_popens]

    logging.info("All workers have terminated. Shutting down.")


# For SLURM, PBS, etc., I should refactor the strategy used by FireWorks:
#   https://github.com/materialsproject/fireworks/tree/main/fireworks/queue
#
# I tried a hacky approah using dask-jobqueue, but it was just too messy and
# buggy to use in production:
#
# from simmate.configuration.dask import get_dask_client
# from dask.distributed import as_completed
# n_workers = 5
# client = get_dask_client(n_workers=n_workers, threads_per_worker=1)
# futures = []
# for dask_id, dask_worker in client.cluster.workers.items():
#     future = client.submit(
#         subprocess.run,
#         f"simmate workflow-engine start-singleflow-worker > worker_{dask_id}.out",
#         shell=True,
#         # capture_output=True,
#         pure=False,
#         workers=[dask_id],
#     )
#     future.worker_id = dask_id  # for reference later
#     future.worker_nanny = dask_worker  # for reference later
#     futures.append(future)
# for future in as_completed(futures):
#     print("restarting")
#     future.worker_nanny.restart()
