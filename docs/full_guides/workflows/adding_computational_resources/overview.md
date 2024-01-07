> :warning: This module is intended as a simpler alternative to Prefect. It offers a stable, quick-start solution, but lacks the scalability and comprehensive features of Prefect.

This module functions as an SQL executor, offering a streamlined version of FireWorks and Prefect. The scheduler is directly integrated with the Django database, removing the need to navigate firewalls or intricate setups. Any worker with database access can operate effectively. However, this configuration slows down the executor as each task requires multiple database calls and write operations. This trade-off between speed and stability is acceptable, as many Simmate workflows take longer than a minute, and the speed reduction is less than a second.

Here's how to implement it:

```python
from simmate.engine.execution.executor import SimmateExecutor

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

from simmate.engine.execution.worker import SimmateWorker

worker = SimmateWorker(waittime_on_empty_queue=1, tags=[])  # nitems_max=1
worker.start()

# ----------------------------------------------------------------------------
```