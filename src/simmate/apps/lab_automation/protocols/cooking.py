# -*- coding: utf-8 -*-

from simmate.apps.lab_automation.planners import PreemptableTask, SchedulePlanner, Task


def add_steak_protocol(planner: SchedulePlanner):
    # Add Steak Tasks
    s1 = Task("Season steak", 5, "Chef")
    s2 = Task("Sear steak", 5, ["Chef", "Stove"])
    s3 = Task("Load steak into oven", 1, ["Chef", "Oven"])
    s4 = Task("Roast steak", 15, "Oven")
    s5 = Task("Remove steak from oven", 1, ["Chef", "Oven"])
    s6 = Task("Make pan sauce", 5, ["Chef", "Stove"])

    planner.add_tasks(s1, s2, s3, s4, s5, s6)

    # Apply Dependencies
    planner.add_dependency(s1, s2)
    planner.add_chain(s2, s3, s4, s5, constraint_type="no_wait")
    planner.add_dependency(s5, s6, constraint_type="grace_period", max_delay=5)


def add_souffle_protocol(planner: SchedulePlanner):
    # Add Soufflé Tasks
    c1 = Task("Prep Soufflé", 10, "Chef")
    c2 = Task("Load Soufflé into oven", 1, ["Chef", "Oven"])
    c3 = Task("Bake Soufflé", 25, "Oven")
    c4 = Task("Remove Soufflé from oven", 1, ["Chef", "Oven"])
    c5 = Task("Serve Soufflé", 2, "Chef")

    planner.add_tasks(c1, c2, c3, c4, c5)

    # Apply Dependencies
    planner.add_chain(c1, c2, c3, c4, c5, constraint_type="no_wait")


def add_pasta_protocol(planner: SchedulePlanner):
    # Add Pasta Tasks (With Preemption for Chopping)
    # 20 mins total, split into max 4 chunks of at least 5 mins
    p1 = PreemptableTask(
        "Chop Veggies",
        total_duration=20,
        min_chunk_size=5,
        max_chunks=4,
        resources="Chef",
    )
    p2 = Task("Load Veggies into oven", 1, ["Chef", "Oven"])
    p3 = Task("Roast Veggies", 20, "Oven")
    p4 = Task("Remove Veggies from oven", 1, ["Chef", "Oven"])

    p5 = Task("Fill pot & start boil", 2, ["Chef", "Stove"])
    p6 = Task("Boil Pasta", 15, "Stove")
    p7 = Task("Drain pasta", 2, ["Chef", "Stove"])

    p8 = Task("Toss Pasta", 5, "Chef")

    planner.add_tasks(p1, p2, p3, p4, p5, p6, p7, p8)

    # Apply Dependencies
    # Veggies
    planner.add_dependency(p1, p2)  # Points to the parent task properly
    planner.add_chain(p2, p3, p4, constraint_type="no_wait")

    # Pasta
    planner.add_chain(p5, p6, p7, constraint_type="no_wait")

    # Combine
    planner.add_dependency(p4, p8)
    planner.add_dependency(p7, p8)


def add_eggs_benedict_protocol(planner: SchedulePlanner):
    # Add Eggs Benedict Tasks

    # Split poaching eggs so the Chef isn't just staring at the pot
    eb3_1 = Task("Drop eggs in water", 1, ["Chef", "Stove"])
    eb3_2 = Task("Eggs poach", 4, "Stove")
    eb3_3 = Task("Remove poached eggs", 1, ["Chef", "Stove"])

    eb2 = Task("Make Hollandaise", 5, ["Chef", "Blender"])

    eb4 = Task("Assemble Eggs Benedict", 2, "Chef")

    planner.add_tasks(eb3_1, eb3_2, eb3_3, eb2, eb4)

    # Apply Dependencies
    planner.add_dependency(eb3_1, eb3_2, constraint_type="no_wait")
    planner.add_dependency(eb3_2, eb3_3, constraint_type="grace_period", max_delay=1)

    planner.add_dependency(eb2, eb3_3, constraint_type="sync_ends", max_delay=2)

    planner.add_dependency(eb2, eb4)
    planner.add_dependency(eb3_3, eb4)
