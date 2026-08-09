# -*- coding: utf-8 -*-

from simmate.apps.lab_automation.planners import SchedulePlanner
from simmate.apps.lab_automation.protocols.chemistry import (
    add_exp1_ongoing,
    add_exp2_finished,
    add_exp3_setup,
    add_exp4_setup,
)

planner = SchedulePlanner()

add_exp1_ongoing(planner)
add_exp2_finished(planner)
add_exp3_setup(planner)
add_exp4_setup(planner)

# Run the solver
planner.build_model()
planner.solve()

# Open the Gantt chart in the browser
planner.plot_gantt(title="Chemistry Lab Resource Utilization Timeline")
