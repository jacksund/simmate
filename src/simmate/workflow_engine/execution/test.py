# -*- coding: utf-8 -*-

from simmate.workflow_engine.execution.executor import SimmateExecutor

executor = SimmateExecutor()

# EXAMPLE 1
future = executor.submit(sum, [4, 3, 2, 1])
assert future.result() == 10

# EXAMPLE 2
import time


def test():
    futures = [executor.submit(time.sleep, 5) for n in range(10)]
    return executor.wait(futures)


test()

# ----------------------------------------------------------------------------

from simmate.workflow_engine.execution.worker import SimmateWorker

worker = SimmateWorker(waittime_on_empty_queue=1)  # nitems_max=1
worker.start()

# ----------------------------------------------------------------------------
