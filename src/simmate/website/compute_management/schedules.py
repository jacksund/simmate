# -*- coding: utf-8 -*-

from simmate.compute import schedule
from simmate.compute.worker import SimmateWorker


@schedule(interval="minute", every=5)
def run_update_stale_workers():
    """
    Marks workers that have stopped checking in as "Stale Heartbeat" or
    "Crashed", and interrupts any WorkItems that crashed workers were running.
    """
    SimmateWorker.update_stale_workers()
