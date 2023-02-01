# -*- coding: utf-8 -*-


import subprocess
from pathlib import Path
from tempfile import mkstemp

from simmate.engine.execution.cluster.base import Cluster


class LocalCluster(Cluster):
    """
    Submits workers via subprocesses
    """

    worker_command: str = "simmate engine start-worker"

    @classmethod
    def submit_job(cls) -> subprocess.Popen:
        output_file = (
            Path.cwd()
            / mkstemp(
                prefix="simmate-worker-",
                suffix=".out",
                dir=Path.cwd(),
            )[1]
        )

        popen = subprocess.Popen(
            cls.worker_command,
            shell=True,
            stdout=output_file.open("w"),
            stderr=output_file.open("w"),
        )
        return popen

    @staticmethod
    def update_jobs_list(job_ids: list[subprocess.Popen]) -> list[subprocess.Popen]:
        # each job id is actually a subprocess.Popen object
        still_running = []
        for process in job_ids:
            if process.poll() is None:
                # p.subprocess is alive
                still_running.append(process)

        return still_running
