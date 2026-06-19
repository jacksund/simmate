# -*- coding: utf-8 -*-

from simmate.apps.lab_automation.planners import PreemptableTask, SchedulePlanner, Task


def add_steak_protocol(planner: SchedulePlanner):
    # Add Steak Tasks
    planner.add_task(Task("S1", "Season steak", 5, "Chef"))
    planner.add_task(Task("S2", "Sear steak", 5, ["Chef", "Stove"]))
    planner.add_task(Task("S3", "Load steak into oven", 1, ["Chef", "Oven"]))
    planner.add_task(Task("S4", "Roast steak", 15, "Oven"))
    planner.add_task(Task("S5", "Remove steak from oven", 1, ["Chef", "Oven"]))
    planner.add_task(Task("S6", "Make pan sauce", 5, ["Chef", "Stove"]))

    # Apply Dependencies
    planner.add_dependency("S1", "S2")
    planner.add_dependency("S2", "S3", constraint_type="no_wait")
    planner.add_dependency("S3", "S4", constraint_type="no_wait")
    planner.add_dependency("S4", "S5", constraint_type="no_wait")
    planner.add_dependency("S5", "S6", constraint_type="grace_period", max_delay=5)


def add_souffle_protocol(planner: SchedulePlanner):
    # Add Soufflé Tasks
    planner.add_task(Task("C1", "Prep Soufflé", 10, "Chef"))
    planner.add_task(Task("C2", "Load Soufflé into oven", 1, ["Chef", "Oven"]))
    planner.add_task(Task("C3", "Bake Soufflé", 25, "Oven"))
    planner.add_task(Task("C4", "Remove Soufflé from oven", 1, ["Chef", "Oven"]))
    planner.add_task(Task("C5", "Serve Soufflé", 2, "Chef"))

    # Apply Dependencies
    planner.add_dependency("C1", "C2", constraint_type="no_wait")
    planner.add_dependency("C2", "C3", constraint_type="no_wait")
    planner.add_dependency("C3", "C4", constraint_type="no_wait")
    planner.add_dependency("C4", "C5", constraint_type="no_wait")


def add_pasta_protocol(planner: SchedulePlanner):
    # Add Pasta Tasks (With Preemption for Chopping)
    # 20 mins total, split into four 5-min chunks
    planner.add_task(PreemptableTask("P1", "Chop Veggies", 20, 5, "Chef"))
    planner.add_task(Task("P2", "Load Veggies into oven", 1, ["Chef", "Oven"]))
    planner.add_task(Task("P3", "Roast Veggies", 20, "Oven"))
    planner.add_task(Task("P4", "Remove Veggies from oven", 1, ["Chef", "Oven"]))

    planner.add_task(Task("P5", "Fill pot & start boil", 2, ["Chef", "Stove"]))
    planner.add_task(Task("P6", "Boil Pasta", 15, "Stove"))
    planner.add_task(Task("P7", "Drain pasta", 2, ["Chef", "Stove"]))

    planner.add_task(Task("P8", "Toss Pasta", 5, "Chef"))

    # Apply Dependencies
    # Veggies
    planner.add_dependency("P1", "P2")  # Points to the parent task properly
    planner.add_dependency("P2", "P3", constraint_type="no_wait")
    planner.add_dependency("P3", "P4", constraint_type="no_wait")

    # Pasta
    planner.add_dependency("P5", "P6", constraint_type="no_wait")
    planner.add_dependency("P6", "P7", constraint_type="no_wait")

    # Combine
    planner.add_dependency("P4", "P8")
    planner.add_dependency("P7", "P8")


def add_eggs_benedict_protocol(planner: SchedulePlanner):
    # Add Eggs Benedict Tasks
    planner.add_task(Task("EB1", "Toast Muffin", 3, "Toaster"))

    # Split poaching eggs so the Chef isn't just staring at the pot
    planner.add_task(Task("EB3_1", "Drop eggs in water", 1, ["Chef", "Stove"]))
    planner.add_task(Task("EB3_2", "Eggs poach", 4, "Stove"))
    planner.add_task(Task("EB3_3", "Remove poached eggs", 1, ["Chef", "Stove"]))

    planner.add_task(Task("EB2", "Make Hollandaise", 5, ["Chef", "Blender"]))

    planner.add_task(Task("EB4", "Assemble Eggs Benedict", 2, "Chef"))

    # Apply Dependencies
    planner.add_dependency("EB3_1", "EB3_2", constraint_type="no_wait")
    planner.add_dependency(
        "EB3_2", "EB3_3", constraint_type="grace_period", max_delay=1
    )

    planner.add_dependency("EB1", "EB2", constraint_type="sync_ends", max_delay=2)
    planner.add_dependency("EB2", "EB3_3", constraint_type="sync_ends", max_delay=2)

    planner.add_dependency("EB1", "EB4")
    planner.add_dependency("EB2", "EB4")
    planner.add_dependency("EB3_3", "EB4")
