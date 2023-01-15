# -*- coding: utf-8 -*-

import logging
import subprocess

from simmate.engine.execution.cluster.base import Cluster


class SlurmCluster(Cluster):
    """
    Submits workers via a submit.sh file (in the working directory) and to
    a SLURM cluster.
    """

    @staticmethod
    def submit_job() -> int:
        """
        Submits a new job to the queue and returns the job id
        """
        process = subprocess.run(
            "sbatch submit.sh",
            shell=True,
            capture_output=True,
            text=True,
        )
        job_id = int(process.stdout.strip().split()[-1])
        return job_id

    @staticmethod
    def update_jobs_list(job_ids: list[int]) -> list[int]:
        """
        Given a list of job ids, it will check which ones are still running and
        which are finished. It will then return a list of the job id that are
        still running.
        """

        # OPTIMIZE: is there a way to queue a list of ids?
        still_running = []
        for job_id in job_ids:
            process = subprocess.run(
                f"squeue -j {job_id}",
                shell=True,
                capture_output=True,
                text=True,
            )
            # An error is return if the job is no longer in the queue.
            # If the job is still running, then two lines will be printed to
            # stdout AND the return code will be 0.
            if process.returncode == 0 and process.stdout.count("\n") == 2:
                still_running.append(job_id)
            else:
                logging.info(f"Slurm job {job_id} completed")

        return still_running
