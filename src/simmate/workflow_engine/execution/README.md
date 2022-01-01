> :warning: This module is entirely experimental and should not be used at the moment. Instead, users should configure their computational resources using Prefect.

This is an SQL executor that intends to be a stripped down version of FireWorks. I really like how the database scheduler makes it so you don't have to deal with firewalls -- any worker that can connect to the database will work just fine. This is a big step up over Dask, where I need to mess with ports and firewalls. Dask and Prefect also don't have workers that run one job and then exit.

Example usage:

```python
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
```
