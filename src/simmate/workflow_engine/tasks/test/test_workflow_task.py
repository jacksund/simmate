# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import Workflow, task
from simmate.workflow_engine.tasks.workflow_task import WorkflowTask


@task
def dummy_task_1():
    return 1


@task
def dummy_task_2():
    return 2


def test_workflowtask_1():

    # create a simple workflow
    with Workflow("dummy-flow-1") as flow_1:
        dummy_task_1()

    # convert to a workflow task
    flowtask_1a = WorkflowTask(flow_1)
    
    # also try converting by the method
    flowtask_1b = flow_1.to_workflow_task()

    # run the task independently
    flowtask_1a.run()
    flowtask_1b.run()

    # Put the workflow task within another workflow
    with Workflow("dummy-flow-2") as flow_2:
        flowtask_1a()
        flowtask_1b()
        dummy_task_2()

    # Run the nested workflow
    flow_2.run()
