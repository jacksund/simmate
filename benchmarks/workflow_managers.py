# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------

"""
This tests workflow orchestration! Don't confuse this timetest with Executors.
This code is messy at the moment, but will become much cleaner when I establish
a WorkFlow class.
"""

# -----------------------------------------------------------------------------

# the number of dummy tasks to run in serial and number of total trials
ntasks_range = range(1, 16, 2)
ntrials = 50

# -----------------------------------------------------------------------------

# No Manager
nomanager_times = []
for ntasks in ntasks_range:

    from pymatdisc.test.tasks import dummy

    def flow_dummy():
        for n in range(ntasks):
            dummy()

    # now run the time test
    from timeit import default_timer as time

    trial_times = []
    for x in range(ntrials):
        # start the timer
        start = time()
        # run the flow locally
        flow_dummy()
        # stop the timer
        stop = time()
        # add time to db
        trial_times.append(stop - start)

    nomanager_times.append(trial_times)

import pandas

df_prefect = pandas.DataFrame(nomanager_times).transpose()
df_prefect.columns = ["ntasks_{}".format(i) for i in ntasks_range]
df_prefect.to_csv("nomanager_times.csv")

# -----------------------------------------------------------------------------

# Prefect Local Testing (no local or cloud server)
prefect_local_times = []
for ntasks in ntasks_range:

    from prefect import Flow
    from pymatdisc.test.tasks import dummy_task

    # flow = Flow("dummy-flow", tasks=[dummy_task]*ntasks) # this doesn't work. it only makes one task...
    with Flow("dummy-flow") as flow:
        for n in range(ntasks):
            dummy_task()

    # now run the time test
    from timeit import default_timer as time

    trial_times = []
    for x in range(ntrials):
        # start the timer
        start = time()
        # run the flow locally
        flow.run()
        # stop the timer
        stop = time()
        # add time to db
        trial_times.append(stop - start)

    prefect_local_times.append(trial_times)

import pandas

df_prefect = pandas.DataFrame(prefect_local_times).transpose()
df_prefect.columns = ["ntasks_{}".format(i) for i in ntasks_range]
df_prefect.to_csv("prefect_local_times.csv")

# -----------------------------------------------------------------------------

# FireWorks Testing (MongoDB server)
fireworks_times = []
for ntasks in ntasks_range:

    # Connect to launchpad database
    from fireworks import LaunchPad

    launchpad = LaunchPad.from_file("my_launchpad.yaml")

    # Establish the benchmark workflow for Dummy runs
    from fireworks import Firework, Workflow
    from pymatdisc.test.tasks import DummyTask

    # create the FireWorks and Workflow
    fireworks = [Firework(DummyTask(), name="dummy") for n in range(ntasks)]

    # create the FireWorks' links (for serial execution)
    fireworks_links = {}
    for i, fw in enumerate(fireworks[:-1]):
        fireworks_links.update({fw: [fireworks[i + 1]]})

    # create the workflow
    workflow = Workflow(fireworks, fireworks_links, name="dummy workflow")

    # reset the database before time testing
    launchpad.reset("", require_password=False)

    # now run the time test
    from fireworks.core.rocket_launcher import rapidfire
    from timeit import default_timer as time

    trial_times = []
    for x in range(ntrials):
        # start the timer
        start = time()
        # add the workflow to the database
        launchpad.add_wf(workflow)
        # run the workflow locally
        rapidfire(launchpad)  # strm_lvl='ERROR'
        # delete the wf so database doesn't overflow
        launchpad.delete_wf(
            workflow.fws[0].fw_id
        )  # I need to delete via a FireWork id...
        # stop the timer
        stop = time()
        # add time to db
        trial_times.append(stop - start)

    fireworks_times.append(trial_times)

import pandas

df_fireworks = pandas.DataFrame(fireworks_times).transpose()
df_fireworks.columns = ["ntasks_{}".format(i) for i in ntasks_range]
df_fireworks.to_csv("fireworks_times.csv")

# -----------------------------------------------------------------------------

# PLOT RESULTS

mapping = ["nomanager", "prefect_local", "fireworks"]

import pandas

dfs = []
for name in mapping:
    df = pandas.read_csv("{}_times.csv".format(name), index_col=0)
    dfs.append(df)


import plotly.graph_objects as go
from plotly.offline import plot

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
