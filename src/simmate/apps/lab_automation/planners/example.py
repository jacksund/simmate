# -*- coding: utf-8 -*-

import collections

import pandas as pd
import plotly.express as px
from ortools.sat.python import cp_model

# --- 1. Class Definitions ---


class Task:
    """Represents a standard, continuous task."""

    def __init__(self, task_id, name, duration, resources):
        self.task_id = task_id
        self.name = name
        self.duration = duration
        self.resources = resources if isinstance(resources, list) else [resources]

        # Placeholders for OR-Tools variables
        self.start_var = None
        self.end_var = None
        self.interval_var = None


class PreemptableTask:
    """Represents a task that can be paused by splitting it into sequential chunks."""

    def __init__(self, task_id, name, total_duration, chunk_size, resources):
        self.task_id = task_id
        self.name = name
        self.resources = resources if isinstance(resources, list) else [resources]
        self.chunks = []

        # Create standard Tasks for each chunk
        num_chunks = total_duration // chunk_size
        for i in range(num_chunks):
            chunk_task = Task(
                f"{task_id}_{i+1}", f"{name} (Part {i+1})", chunk_size, resources
            )
            self.chunks.append(chunk_task)


# --- 2. The Scheduler Class ---


class KitchenScheduler:
    def __init__(self):
        self.model = cp_model.CpModel()
        self.tasks = (
            {}
        )  # Stores all executable units (standard tasks + individual chunks)
        self.parent_tasks = {}  # Stores overarching parent references
        self.dependencies = []
        self.resources_usage = collections.defaultdict(list)
        self.horizon = 0  # Maximum possible time (sum of all durations)
        self.schedule_data = []  # Stores the solved schedule for plotting

    def add_task(self, task):
        # Store the parent reference
        self.parent_tasks[task.task_id] = task

        if isinstance(task, PreemptableTask):
            for chunk in task.chunks:
                self.tasks[chunk.task_id] = chunk
                self.horizon += chunk.duration

            # Enforce internal order of chunks (Part 1 -> Part 2 -> Part 3...)
            for i in range(len(task.chunks) - 1):
                self.add_dependency(task.chunks[i].task_id, task.chunks[i + 1].task_id)
        else:
            self.tasks[task.task_id] = task
            self.horizon += task.duration

    def add_dependency(self, from_id, to_id, constraint_type="normal", max_delay=0):
        self.dependencies.append(
            {
                "from": from_id,
                "to": to_id,
                "type": constraint_type,
                "max_delay": max_delay,
            }
        )

    def build_model(self):
        # 1. Create Variables for each executable task
        for task_id, task in self.tasks.items():
            task.start_var = self.model.NewIntVar(0, self.horizon, f"start_{task_id}")
            task.end_var = self.model.NewIntVar(0, self.horizon, f"end_{task_id}")
            task.interval_var = self.model.NewIntervalVar(
                task.start_var, task.duration, task.end_var, f"interval_{task_id}"
            )

            # Map intervals to their required resources
            for res in task.resources:
                self.resources_usage[res].append(task.interval_var)

        # 2. Apply Resource Constraints (No-Overlap)
        for resource, intervals in self.resources_usage.items():
            self.model.AddNoOverlap(intervals)

        # 3. Apply Dependencies
        for dep in self.dependencies:

            # Helper function to find the correct start and end variables
            def get_vars(t_id):
                if t_id in self.tasks:
                    # It's a standard task or specific chunk
                    return self.tasks[t_id].start_var, self.tasks[t_id].end_var
                elif t_id in self.parent_tasks:
                    # It's a parent PreemptableTask
                    parent = self.parent_tasks[t_id]
                    if isinstance(parent, PreemptableTask):
                        return parent.chunks[0].start_var, parent.chunks[-1].end_var
                raise ValueError(f"Task ID {t_id} not found!")

            from_start, from_end = get_vars(dep["from"])
            to_start, to_end = get_vars(dep["to"])

            if dep["type"] == "normal":
                self.model.Add(to_start >= from_end)
            elif dep["type"] == "no_wait":
                self.model.Add(to_start == from_end)
            elif dep["type"] == "grace_period":
                self.model.Add(to_start >= from_end)
                self.model.Add(to_start <= from_end + dep["max_delay"])
            elif dep["type"] == "sync_ends":
                self.model.Add(to_end - from_end <= dep["max_delay"])
                self.model.Add(from_end - to_end <= dep["max_delay"])

        # 4. Set Objective: Minimize Makespan
        obj_var = self.model.NewIntVar(0, self.horizon, "makespan")
        self.model.AddMaxEquality(obj_var, [t.end_var for t in self.tasks.values()])
        self.model.Minimize(obj_var)

    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(
                f"Optimal Schedule Found! Total Time: {solver.ObjectiveValue()} minutes\n"
            )

            # 1. Generate Terminal Output (Grouped Resources)
            terminal_output = []
            for t_id, t in self.tasks.items():
                terminal_output.append(
                    {
                        "start": solver.Value(t.start_var),
                        "end": solver.Value(t.end_var),
                        "name": t.name,
                        "resources": t.resources,
                    }
                )

            for task in sorted(terminal_output, key=lambda x: (x["start"], x["name"])):
                print(
                    f"Minute {task['start']:02d} to {task['end']:02d} | {task['name']} | Uses: {', '.join(task['resources'])}"
                )

            # 2. Save Data for Plotly (Exploded Resources)
            self.schedule_data = []
            for t_id, t in self.tasks.items():
                start_time = solver.Value(t.start_var)
                end_time = solver.Value(t.end_var)

                # If a task uses multiple resources, create a block for EACH resource lane
                for res in t.resources:
                    self.schedule_data.append(
                        {
                            "Task": t.name,
                            "Start": start_time,
                            "End": end_time,
                            "Duration": end_time - start_time,
                            "Resource": res,
                        }
                    )
        else:
            print("No feasible schedule found. Constraints are too tight!")

    def plot_gantt(self):
        """Generates and opens a Resource Utilization chart in the browser using Plotly."""
        if not self.schedule_data:
            print("No schedule data to plot. Please run solve() first.")
            return

        # Convert to Pandas DataFrame
        df = pd.DataFrame(self.schedule_data)

        # Sort tasks so overlaps and legends render cleanly
        # Sorting by Resource then Start time maps well to a horizontal layout
        df = df.sort_values(by=["Resource", "Start"], ascending=[True, True])

        # Create horizontal bar chart: Time on X-axis, Resources on Y-axis
        fig = px.bar(
            df,
            x="Duration",  # Length of the bar represents Time
            y="Resource",  # Resources mapped to the Y-axis lanes
            base="Start",  # Where the bar begins (X-axis offset)
            color="Task",  # Color code by the specific Recipe Task
            orientation="h",  # Set bars to flow horizontally
            title="Kitchen Resource Utilization Timeline",
            hover_data=["Start", "End"],
            text="Task",  # Labels the bars directly for easier reading
        )

        # Polish the visual layout
        fig.update_layout(
            xaxis_title="Time (Minutes)",
            yaxis_title="Resources",
            showlegend=True,
            plot_bgcolor="rgba(240, 240, 240, 0.8)",
            barmode="overlay",
        )

        # Center the text inside the bars (removed the -90 rotation so it reads left-to-right)
        fig.update_traces(textposition="inside", insidetextanchor="middle")

        # Render in the default web browser
        fig.show(renderer="browser")


# --- 3. Workflow Definitions ---


def add_steak_workflow(scheduler):
    # Add Steak Tasks
    scheduler.add_task(Task("S1", "Season steak", 5, ["Chef"]))
    scheduler.add_task(Task("S2", "Sear steak", 5, ["Chef", "Stove"]))
    scheduler.add_task(Task("S3", "Load steak into oven", 1, ["Chef", "Oven"]))
    scheduler.add_task(Task("S4", "Roast steak", 15, ["Oven"]))
    scheduler.add_task(Task("S5", "Remove steak from oven", 1, ["Chef", "Oven"]))
    scheduler.add_task(Task("S6", "Make pan sauce", 5, ["Chef", "Stove"]))

    # Apply Dependencies
    scheduler.add_dependency("S1", "S2")
    scheduler.add_dependency("S2", "S3", constraint_type="no_wait")
    scheduler.add_dependency("S3", "S4", constraint_type="no_wait")
    scheduler.add_dependency("S4", "S5", constraint_type="no_wait")
    scheduler.add_dependency("S5", "S6", constraint_type="grace_period", max_delay=5)


def add_souffle_workflow(scheduler):
    # Add Soufflé Tasks
    scheduler.add_task(Task("C1", "Prep Soufflé", 10, ["Chef"]))
    scheduler.add_task(Task("C2", "Load Soufflé into oven", 1, ["Chef", "Oven"]))
    scheduler.add_task(Task("C3", "Bake Soufflé", 25, ["Oven"]))
    scheduler.add_task(Task("C4", "Remove Soufflé from oven", 1, ["Chef", "Oven"]))
    scheduler.add_task(Task("C5", "Serve Soufflé", 2, ["Chef"]))

    # Apply Dependencies
    scheduler.add_dependency("C1", "C2", constraint_type="no_wait")
    scheduler.add_dependency("C2", "C3", constraint_type="no_wait")
    scheduler.add_dependency("C3", "C4", constraint_type="no_wait")
    scheduler.add_dependency("C4", "C5", constraint_type="no_wait")


def add_pasta_workflow(scheduler):
    # Add Pasta Tasks (With Preemption for Chopping)
    # 20 mins total, split into four 5-min chunks
    scheduler.add_task(PreemptableTask("P1", "Chop Veggies", 20, 5, ["Chef"]))
    scheduler.add_task(Task("P2", "Load Veggies into oven", 1, ["Chef", "Oven"]))
    scheduler.add_task(Task("P3", "Roast Veggies", 20, ["Oven"]))
    scheduler.add_task(Task("P4", "Remove Veggies from oven", 1, ["Chef", "Oven"]))

    scheduler.add_task(Task("P5", "Fill pot & start boil", 2, ["Chef", "Stove"]))
    scheduler.add_task(Task("P6", "Boil Pasta", 15, ["Stove"]))
    scheduler.add_task(Task("P7", "Drain pasta", 2, ["Chef", "Stove"]))

    scheduler.add_task(Task("P8", "Toss Pasta", 5, ["Chef"]))

    # Apply Dependencies
    # Veggies
    scheduler.add_dependency("P1", "P2")  # Points to the parent task properly
    scheduler.add_dependency("P2", "P3", constraint_type="no_wait")
    scheduler.add_dependency("P3", "P4", constraint_type="no_wait")

    # Pasta
    scheduler.add_dependency("P5", "P6", constraint_type="no_wait")
    scheduler.add_dependency("P6", "P7", constraint_type="no_wait")

    # Combine
    scheduler.add_dependency("P4", "P8")
    scheduler.add_dependency("P7", "P8")


def add_eggs_benedict_workflow(scheduler):
    # Add Eggs Benedict Tasks
    scheduler.add_task(Task("EB1", "Toast Muffin", 3, ["Toaster"]))

    # Split poaching eggs so the Chef isn't just staring at the pot
    scheduler.add_task(Task("EB3_1", "Drop eggs in water", 1, ["Chef", "Stove"]))
    scheduler.add_task(Task("EB3_2", "Eggs poach", 4, ["Stove"]))
    scheduler.add_task(Task("EB3_3", "Remove poached eggs", 1, ["Chef", "Stove"]))

    scheduler.add_task(Task("EB2", "Make Hollandaise", 5, ["Chef", "Blender"]))

    scheduler.add_task(Task("EB4", "Assemble Eggs Benedict", 2, ["Chef"]))

    # Apply Dependencies
    scheduler.add_dependency("EB3_1", "EB3_2", constraint_type="no_wait")
    scheduler.add_dependency(
        "EB3_2", "EB3_3", constraint_type="grace_period", max_delay=1
    )

    scheduler.add_dependency("EB1", "EB2", constraint_type="sync_ends", max_delay=2)
    scheduler.add_dependency("EB2", "EB3_3", constraint_type="sync_ends", max_delay=2)

    scheduler.add_dependency("EB1", "EB4")
    scheduler.add_dependency("EB2", "EB4")
    scheduler.add_dependency("EB3_3", "EB4")


# --- 4. Executing the Example ---

if __name__ == "__main__":
    scheduler = KitchenScheduler()

    add_steak_workflow(scheduler)
    add_souffle_workflow(scheduler)
    add_pasta_workflow(scheduler)
    add_eggs_benedict_workflow(scheduler)

    # Run the solver
    scheduler.build_model()
    scheduler.solve()

    # Open the Gantt chart in the browser
    scheduler.plot_gantt()
