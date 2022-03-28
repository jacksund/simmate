# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------

"""
This tests workflow execution. For simplicity, the "workflow" here is only a 
pass statement. Thus the times show us the overhead caused by the executor.
"""

#!!! Will this overhead change as the number of workers change...?

# -----------------------------------------------------------------------------

# the number of dummy tasks to run in serial and number of total trials
ntrials = 500
# nworkers = range(1,4) #!!! since executors support parallelism, I should test scaling the workers as well

from timeit import default_timer as time


def dummy_workflow():
    pass


#!!! I need to change this if I'm switching to test multiple workers
#!!! Switch to submitting all trials at once, then waiting on futures, then report an average/stdev
def executor_time_test(executor, ntrials):
    trial_times = []
    for _ in range(ntrials):
        start = time()
        future = executor.submit(dummy_workflow)
        while executor.check(future) != "done":
            pass
        executor.get_result(future)  # result = ...
        stop = time()
        trial_times.append(stop - start)
    return trial_times  #!!! The first trial takes longer for every executor -- should I remove it?


# -----------------------------------------------------------------------------

# Local Executor
from pymatdisc.engine.executors import LocalExecutor

localexec = LocalExecutor()
localexec_times = executor_time_test(localexec, ntrials)

# import pandas
# df_prefect = pandas.DataFrame(nomanager_times).transpose()
# df_prefect.columns = ['ntasks_{}'.format(i) for i in ntasks_range]
# df_prefect.to_csv('nomanager_times.csv')

# -----------------------------------------------------------------------------

# Dask Executor (local and single worker)

# setup the cluster with only one worker
from dask.distributed import LocalCluster

cluster = LocalCluster(n_workers=1, threads_per_worker=1)

from pymatdisc.engine.executors import DaskExecutor

daskexec = DaskExecutor(cluster.scheduler_address)  # address = None
daskexec_times = executor_time_test(daskexec, ntrials)

# -----------------------------------------------------------------------------

# # FireWorks Executor

# #!!! NOTE -- Fireworks requires a string as the func input, not the actual function!
# def fwexecutor_time_test(executor, ntrials):
#     trial_times = []
#     for _ in range(ntrials):
#         start = time()
#         future = executor.submit('pymatdisc.test.tasks.dummy')
#         while executor.check(future) != 'done':
#             pass
#         executor.get_result(future) # result = ...
#         stop = time()
#         trial_times.append(stop-start)
#     return trial_times #!!! The first trial takes longer for every executor -- should I remove it?

# #!!! In a separate terminal, I need a fireworks worker running!
# #!!! I also need to make sure the working directory has my fireworks config yaml

# from pymatdisc.engine.executors import FireWorksExecutor
# fwexec = FireWorksExecutor()
# fwexec_times = fwexecutor_time_test(fwexec, ntrials)

# -----------------------------------------------------------------------------
