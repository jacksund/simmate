# -*- coding: utf-8 -*-

from prefect import Flow, Parameter

from simmate.calculators.vasp.tasks.prebader import VASPPreBaderTask
from simmate.calculators.bader.tasks import BaderAnalysisTask

# we need to initialize the Prefect task classes that we will be using
vasp_prebader_task = VASPPreBaderTask()
bader_analysis_task = BaderAnalysisTask()

# If I wanted both of these tasks to run together as a single task, then I can
# wrap them into a single function. This is the equivalent of taking multiple
# Fireworks/Firetasks and wrapping them into one Firework! I could even
# wrap an entire workflow into a single task here.
#   @task
#   def full_bader_analysis_task():
#       VASPPreBaderTask().run()
#       BaderAnalysisTask().run()
# Likewise, Fireworks has FireTasks where we only have simple functions here.
# If I want to make a function into an individual task, I simply use the
# decorator task like this: my_task = task(my_function)

# now make the overall workflow
with Flow("BaderAnalysis") as workflow:

    # take structure as an input for this workflow
    structure = Parameter("structure")

    # run a "PreBader" VASP calculation
    vasp_output = vasp_prebader_task(structure=structure)

    # run Bader Analysis on the output
    # Also make sure that Bader doesn't run until VASP completes. We need to
    # set this explicitly becuase no variable is passed between the two tasks
    bader_output = bader_analysis_task(upstream_tasks=[vasp_output])

# workflow.visualize()
