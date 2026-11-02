from simmate.compute import SimmateWorker, WorkItem, schedule
from simmate.config import settings
from simmate.utils import logger
from simmate.workflows.common import Maintenance__Postgres__BackupToS3


@schedule(interval="minute", every=5)
def run_update_stale_workers():
    """
    Marks workers that have stopped checking in as "Stale Heartbeat" or
    "Crashed", and interrupts any WorkItems that crashed workers were running.
    """
    SimmateWorker.update_stale_workers()


@schedule(interval="daily", at="04:00")
def run_delete_inactive_compute_entries():
    """
    Nightly cleanup of finished WorkItems and inactive workers that haven't
    been updated in over 30 days.
    """
    # items go first so fewer rows need their worker link nulled out
    nitems = WorkItem.delete_inactive()
    nworkers = SimmateWorker.delete_inactive()
    logger.info(f"Deleted {nitems} old WorkItem(s) and {nworkers} old worker(s)")


if settings.database_backups:

    @schedule(interval="daily", at="03:00")
    def run_database_backup():
        """
        Nightly backup of the database to the private s3 bucket. Requires
        postgres and `settings.s3.bucket`.

        Enable with `database_backups: true` in your settings.
        """
        Maintenance__Postgres__BackupToS3.run()
