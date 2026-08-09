# -*- coding: utf-8 -*-

from simmate.apps.lab_automation.planners import SchedulePlanner
from simmate.apps.lab_automation.planners.tasks import FixedTask, Task


def add_exp1_ongoing(planner: SchedulePlanner):
    """Experiment 1: Ongoing and set to finish mid-day (t=240)."""
    # Started 120 mins ago, duration 360, ends at 240
    t1 = FixedTask("Exp1: Heating Reaction", 360, -120, "Hotplate 1")
    t2 = Task("Exp1: Cool to RT", 30, "Hotplate 1")
    t3 = Task("Exp1: Liquid-Liquid Extraction", 45, ["Chemist", "Fume Hood"])
    t4 = Task("Exp1: Rotovap Solvent", 40, ["Chemist", "Rotovap"])
    t5 = Task("Exp1: Prep & Run NMR", 20, ["Chemist", "NMR"])

    planner.add_tasks(t1, t2, t3, t4, t5)

    planner.add_dependency(t1, t2, constraint_type="no_wait")
    planner.add_chain(t2, t3, t4, t5)


def add_exp2_finished(planner: SchedulePlanner):
    """Experiment 2: Finished and ready for workup right now."""
    # Simulating it finished right at t=0
    t1 = FixedTask("Exp2: Overnight Reaction", 480, -480, "Hotplate 2")
    t2 = Task("Exp2: Quench Reaction", 15, ["Chemist", "Fume Hood"])
    t3 = Task("Exp2: Vacuum Filtration", 25, ["Chemist", "Fume Hood"])
    t4 = Task("Exp2: Dry in Vacuum Oven", 180, "Vacuum Oven")
    t5 = Task("Exp2: Weigh Yield", 10, ["Chemist", "Balance"])

    planner.add_tasks(t1, t2, t3, t4, t5)

    planner.add_dependency(t1, t2, constraint_type="no_wait")
    planner.add_dependency(t2, t3)
    planner.add_dependency(t3, t4, constraint_type="no_wait")
    planner.add_dependency(t4, t5)


def add_exp3_setup(planner: SchedulePlanner):
    """Experiment 3: Needs full setup."""
    t1 = Task("Exp3: Gather Reagents", 10, "Chemist")
    t2 = Task("Exp3: Weigh Reactants", 15, ["Chemist", "Balance"])
    t3 = Task("Exp3: Setup Glassware", 20, ["Chemist", "Fume Hood"])
    t4 = Task("Exp3: Run Reaction", 180, "Hotplate 3")
    t5 = Task("Exp3: Quick Extraction", 30, ["Chemist", "Fume Hood"])

    planner.add_tasks(t1, t2, t3, t4, t5)

    planner.add_chain(t1, t2, t3, t4, constraint_type="no_wait")
    planner.add_dependency(t4, t5)


def add_exp4_setup(planner: SchedulePlanner):
    """Experiment 4: Needs full setup."""
    t1 = Task("Exp4: Gather Reagents", 10, "Chemist")
    t2 = Task("Exp4: Weigh Reactants", 20, ["Chemist", "Balance"])
    t3 = Task("Exp4: Setup Glassware", 15, ["Chemist", "Fume Hood"])
    t4 = Task("Exp4: Run Reaction", 120, "Hotplate 4")
    t5 = Task("Exp4: Filtration", 20, ["Chemist", "Fume Hood"])

    planner.add_tasks(t1, t2, t3, t4, t5)

    planner.add_chain(t1, t2, t3, t4, constraint_type="no_wait")
    planner.add_dependency(t4, t5)
