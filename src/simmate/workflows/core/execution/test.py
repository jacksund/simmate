# -*- coding: utf-8 -*-

from simmate.configuration.manage_django import reset_db

reset_db()

from simmate.workflows.core.execution.executor import DjangoExecutor

executor = DjangoExecutor()

future = executor.submit(sum, [1, 2, 3, 4])

# ----------------------------------------------------------------------------

from simmate.workflows.core.execution.worker import DjangoWorker

worker = DjangoWorker(nitems_max=1)
worker.start()

# ----------------------------------------------------------------------------

assert future.result() == 10

# ----------------------------------------------------------------------------
