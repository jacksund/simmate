# -*- coding: utf-8 -*-

from simmate.compute import schedule
from simmate.compute.worker import SimmateWorker
from simmate.config import settings
from simmate.workflows.common import Maintenance__Postgres__BackupToS3


@schedule(interval="minute", every=5)
def run_update_stale_workers():
    """
    Marks workers that have stopped checking in as "Stale Heartbeat" or
    "Crashed", and interrupts any WorkItems that crashed workers were running.
    """
    SimmateWorker.update_stale_workers()


if settings.database_backups:

    @schedule(interval="daily", at="03:00")
    def run_database_backup():
        """
        Nightly backup of the database to the private s3 bucket. Requires
        postgres and `settings.s3.bucket`.

        Enable with `database_backups: true` in your settings.
        """
        Maintenance__Postgres__BackupToS3.run()
