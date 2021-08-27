Beginners beware! This module is pretty advanced and can be confusing for some. You should go through the tutorials in each submodule of this folder -- it will save you a lot of headache down the road.

This module is really just an extenstion of Prefect (simmate's core for tasks and workflows) and Dask (simmate's core for parallel exectution). Therefore the code located here are the missing components of those two libraries. 

The first is robust error handling of a given Prefect task, which is done very well in the Custodian library. I take concepts from that library and rewrite it in the simmate.workflow_engine.tasks module.

The second is an Executor that can easily get around many HPC clusters that have firewalls. It's a convient way to distribute Prefect tasks accross a bunch of slurm jobs and even accross multiple different clusters/computers without having to deal with extremely complex firewalls of such systems. The simmate.workflow_engine.execution module is really a rewrite and (extremely) stripped down version of FireWorks.

For reference, both FireWorks and Custodian are from the Materials project, which (for a number of reasons discussed elsewhere -- add a link here) I decided to rewrite.


In order to run some Prefect workflows that use Django ORM, we need to make sure each Dask worker has Django properly configured. I can do this a number of ways, where the easiest for the user is just to have all django-related import inside of the task functions. I need to check if this is faster/cleaner compared to using a WorkerPlugin -- which would result in cleaner code (module imports can be outside of the tasks and at the top of the file) but will make things more difficult for the user as they need to make sure they setup Dask in the following way:
```python
from dask.distributed import Client
from distributed.diagnostics.plugin import WorkerPlugin

class SimmateDatabasePlugin(WorkerPlugin):
    def setup(self, worker):
        from simmate.configuration import manage_django  # ensures django setup

client = Client()
client.register_worker_plugin(SimmateDatabasePlugin())
```
