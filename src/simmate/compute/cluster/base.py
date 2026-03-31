# -*- coding: utf-8 -*-

import logging
import time


class Cluster:
    @classmethod
    def start_cluster(cls, nworkers: int, sleep_step: float = 5):
        logging.info(f"Starting cluster with {nworkers} workers")

        # on start-up we need to submit the target number of jobs
        job_ids = cls.submit_jobs(nworkers)

        # we now monitor the jobs running and submit new workers whenever
        # we drop below out target.
        # We do this endlessly until the user closes the script
        while True:
            job_ids = cls.update_jobs_list(job_ids)
            njobs_needed = nworkers - len(job_ids)
            if njobs_needed > 0:
                job_ids += cls.submit_jobs(njobs_needed)
            time.sleep(sleep_step)

    @classmethod
    def wait_for_jobs(cls, job_ids: list[int], sleep_step: float = 5):
        # loop until the job id list is empty
        while job_ids:
            job_ids = cls.update_jobs_list(job_ids)
            time.sleep(sleep_step)

    @classmethod
    def submit_jobs(cls, njobs: int) -> list[int]:
        """
        Calls submit_to_queue a set number of times and returns the new job ids
        """
        job_ids = [cls.submit_job() for n in range(njobs)]
        logging.info(f"{njobs} new workers have been submitted")
        return job_ids

    @staticmethod
    def submit_job() -> int:
        """
        Submits a new job to the queue and returns the job id
        """
        raise NotImplementedError(
            "add a custom submit_job method to your cluster class"
        )

    @staticmethod
    def update_jobs_list(job_ids: list[int]) -> int:
        """
        Given a list of job ids, it will check which ones are still running and
        which are finished. It will then return a list of the job id that are
        still running.
        """
        raise NotImplementedError(
            "add a custom update_jobs_list method to your cluster class"
        )
