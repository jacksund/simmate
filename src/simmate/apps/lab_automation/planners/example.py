# -*- coding: utf-8 -*-

from simmate.apps.lab_automation.planners import SchedulePlanner
from simmate.apps.lab_automation.protocols.cooking import (
    add_eggs_benedict_protocol,
    add_pasta_protocol,
    add_souffle_protocol,
    add_steak_protocol,
)

planner = SchedulePlanner()

add_steak_protocol(planner)
add_souffle_protocol(planner)
add_pasta_protocol(planner)
add_eggs_benedict_protocol(planner)

# Run the solver
planner.build_model()
planner.solve()

# Open the Gantt chart in the browser
planner.plot_gantt(title="Kitchen Resource Utilization Timeline")
