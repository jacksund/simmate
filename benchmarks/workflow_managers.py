# -*- coding: utf-8 -*-

"""
This script tests workflow orchestration -- that is, the submission of workflows
to arbitrary resources. For now, the benchmark looks at a `workflow.run()` which
does nothing (using `pass`). We compare the following:
    - a function written in python
    - a workflow written with Simmate and ran locally

These benchmarks have not been added yet due to extra setup required:
    - a workflow written with Simmate and ran through Prefect Cloud + local Agent
    - a workflow written in FireWorks and ran through a MongoDB Cloud + local Worker
"""

import pandas
from timeit import default_timer as time

# the number of dummy tasks to run in serial and number of total trials
ntasks_range = range(1, 16, 2)
ntrials = 50


def run_trials(fxn, ntrials):
    trial_times = []
    for x in range(ntrials):
        start = time()
        fxn()
        stop = time()
        trial_times.append(stop - start)
    return trial_times


def write_to_csv(times, name):
    df = pandas.DataFrame(times).transpose()
    df.columns = [f"ntasks_{i}" for i in ntasks_range]
    df.to_csv(f"{name}_times.csv")


# -----------------------------------------------------------------------------

# a function written in python with no manager

nomanager_times = []
for ntasks in ntasks_range:

    # build the dummy workflow that simply `passes` N times
    def flow_dummy():
        for n in range(ntasks):
            pass

    # now run the time test
    trial_times = run_trials(flow_dummy, ntrials)
    nomanager_times.append(trial_times)

write_to_csv(nomanager_times, name="nomanager")

# -----------------------------------------------------------------------------

# a workflow written with Simmate and ran locally

from simmate.workflow_engine import Workflow, task

simmate_local_times = []
for ntasks in ntasks_range:

    # build the dummy workflow that simply `passes` N times
    @task
    def dummy_task():
        pass

    with Workflow("dummy-flow") as flow:
        for n in range(ntasks):
            dummy_task()

    # now run the time test
    trial_times = run_trials(flow.run, ntrials)
    simmate_local_times.append(trial_times)

write_to_csv(simmate_local_times, name="simmate_local")

# -----------------------------------------------------------------------------

# a workflow written with Simmate and ran through Prefect Cloud + local Agent

# TODO

# -----------------------------------------------------------------------------

# a workflow written in FireWorks and ran through a MongoDB Cloud + local Worker

# from fireworks.core.rocket_launcher import rapidfire
# from fireworks import LaunchPad, FiretaskBase, Firework, Workflow

# # BUG: This may need to be defined in a different module
# from fireworks.utilities.fw_utilities import explicit_serialize
# @explicit_serialize
# class DummyTask(FiretaskBase):
#     def run_task(self, fw_spec):
#         pass

# fireworks_times = []
# for ntasks in ntasks_range:

#     # Connect to launchpad database
#     launchpad = LaunchPad.from_file("fireworks_server.yaml")
#     launchpad.reset("", require_password=False)

#     # create the FireWorks and Workflow
#     fireworks = [Firework(DummyTask(), name="dummy") for n in range(ntasks)]

#     # create the FireWorks' links (for serial execution)
#     fireworks_links = {}
#     for i, fw in enumerate(fireworks[:-1]):
#         fireworks_links.update({fw: [fireworks[i + 1]]})

#     # create the workflow
#     workflow = Workflow(fireworks, fireworks_links, name="dummy workflow")

#     # reset the database before time testing
#     launchpad.reset("", require_password=False)

#     def run_flow():
#         # add the workflow to the database
#         launchpad.add_wf(workflow)
#         # run the workflow locally
#         rapidfire(launchpad)  # strm_lvl='ERROR'
#         # delete the wf so database doesn't overflow
#         launchpad.delete_wf(
#             workflow.fws[0].fw_id
#         )  # NOTE: This adds extra time to the benchmark

#     # now run the time test
#     trial_times = run_trials(run_flow, ntrials)
#     fireworks_times.append(trial_times)

# write_to_csv(nomanager_times, name="fireworks")

# -----------------------------------------------------------------------------

# PLOT RESULTS

import plotly.graph_objects as go
from plotly.offline import plot

mapping = ["nomanager", "prefect_local"]  # , "fireworks"

dfs = []
for name in mapping:
    df = pandas.read_csv("{}_times.csv".format(name), index_col=0)
    dfs.append(df)

composition_strs = ["ntasks_{}".format(i) for i in ntasks_range]

data = []

for name, df in zip(mapping, dfs):
    # y should be all time values for ALL compositions put together in to a 1D array
    ys = df.values.flatten(order="F")
    # x should be labels that are the same length as the xs list
    xs = []
    for c in composition_strs:
        xs += [c] * ntrials

    series = go.Box(
        name=name,
        x=xs,
        y=ys,
        boxpoints=False,  # look at strip plots if you want the scatter points
    )
    data.append(series)


layout = go.Layout(
    width=800,
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    boxmode="group",
    xaxis=dict(
        title_text="Number of Tasks per Workflow",
        showgrid=False,
        ticks="outside",
        tickwidth=2,
        showline=True,
        color="black",
        linecolor="black",
        linewidth=2,
        mirror=True,
    ),
    yaxis=dict(
        title_text="Time per Workflow (s)",
        type="log",
        ticks="outside",
        tickwidth=2,
        showline=True,
        linewidth=2,
        color="black",
        linecolor="black",
        mirror=True,
    ),
    legend=dict(
        x=0.05,
        y=0.95,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    ),
)

fig = go.Figure(data=data, layout=layout)

plot(fig, config={"scrollZoom": True})

# -----------------------------------------------------------------------------
