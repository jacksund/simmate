# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import Workflow, task


@task
def dummy_task_1():
    return 1


@task
def dummy_task_2():
    return 2


def test_workflowtask_1():

    # Run the workflow just like you would for the base Prefect class
    with Workflow("dummy-flow") as flow:
        dummy_task_1()
        dummy_task_2()
    flow.run()


# TODO: Many of the features I added on based on submitting to Prefect Cloud.
# How to I simulate registering and then submitting a workflow to a server?
