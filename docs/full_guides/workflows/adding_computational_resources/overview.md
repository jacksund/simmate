
> :warning: This module represents an alternative to Prefect. It is meant to be a stable quick-start alternative, but lacks the scaling and numerous features that Prefect offers.

This is an SQL executor that intends to be a stripped down version of FireWorks and Prefect. The scheduler is directly built into the django database, which makes it so you don't have to deal with firewalls or complex setups -- any worker that can connect to the database will work just fine. The downside is that the executor is slower (bc each task requires multiple database calls and also writing to the database). It's a trade off of speed for stability, but this is okay because many workflows in Simmate are >1min and the speed penality is well below 1 second.

Example usage:

```python
from simmate.workflow_engine.execution.executor import SimmateExecutor

# EXAMPLE 1
future = SimmateExecutor.submit(sum, [4, 3, 2, 1])
assert future.result() == 10

# EXAMPLE 2
import time


def test():
    futures = [executor.submit(time.sleep, 5) for n in range(10)]
    return executor.wait(futures)


test()

# ----------------------------------------------------------------------------

from simmate.workflow_engine.execution.worker import SimmateWorker

worker = SimmateWorker(waittime_on_empty_queue=1, tags=[])  # nitems_max=1
worker.start()

# ----------------------------------------------------------------------------
```
