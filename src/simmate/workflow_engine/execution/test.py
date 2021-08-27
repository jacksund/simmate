# -*- coding: utf-8 -*-

from simmate.configuration.django import reset_database

reset_database()

from simmate.workflow_engine.execution.executor import DjangoExecutor

executor = DjangoExecutor()

# EXAMPLE 1
future = executor.submit(sum, [4, 3, 2, 1])
assert future.result() == 10

# EXAMPLE 2
import time


def test():
    futures = [executor.submit(time.sleep, 5) for n in range(10)]
    return executor.wait(futures)


# ----------------------------------------------------------------------------

from simmate.workflow_engine.execution.worker import DjangoWorker

worker = DjangoWorker(waittime_on_empty_queue=1)  # nitems_max=1
worker.start()

# ----------------------------------------------------------------------------
