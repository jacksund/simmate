# -*- coding: utf-8 -*-

import collections

import pandas as pd
import plotly.express as px
from ortools.sat.python import cp_model

from simmate.apps.lab_automation.planners.tasks import PreemptableTask, Task


class SchedulePlanner:
    """Plans and optimizes task execution timelines using OR-Tools."""

    def __init__(self):
        self.model = cp_model.CpModel()
        self.tasks: dict[str, Task] = {}  # All executable chunks
        self.parent_tasks: dict[str, Task | PreemptableTask] = {}  # Top-level tasks
        self.dependencies: list[dict] = []
        self.resources_usage = collections.defaultdict(list)
        self.horizon: int = 0
        self.schedule_data: list[dict] = []

    def add_task(self, task: Task | PreemptableTask):
        self.parent_tasks[task.task_id] = task

        if isinstance(task, PreemptableTask):
            for i, chunk in enumerate(task.chunks):
                self.tasks[chunk.task_id] = chunk
                self.horizon += chunk.duration
                # Enforce sequential chunk execution order
                if i > 0:
                    self.add_dependency(task.chunks[i - 1].task_id, chunk.task_id)
        else:
            self.tasks[task.task_id] = task
            self.horizon += task.duration

    def add_dependency(
        self,
        from_id: str,
        to_id: str,
        constraint_type: str = "normal",
        max_delay: int = 0,
    ):
        self.dependencies.append(
            {
                "from": from_id,
                "to": to_id,
                "type": constraint_type,
                "max_delay": max_delay,
            }
        )

    def _get_start_end_vars(self, task_id: str) -> tuple:
        """Helper to retrieve start/end OR-Tools variables for a given task ID."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return task.start_var, task.end_var
        elif task_id in self.parent_tasks:
            parent = self.parent_tasks[task_id]
            if isinstance(parent, PreemptableTask):
                return parent.chunks[0].start_var, parent.chunks[-1].end_var
        raise ValueError(f"Task ID '{task_id}' not found in scheduler!")

    def build_model(self):
        """Initializes CP variables, resource constraints, and temporal dependencies."""
        # 1. Variables and Resource Mapping
        for task_id, task in self.tasks.items():
            task.start_var = self.model.NewIntVar(0, self.horizon, f"start_{task_id}")
            task.end_var = self.model.NewIntVar(0, self.horizon, f"end_{task_id}")
            task.interval_var = self.model.NewIntervalVar(
                task.start_var, task.duration, task.end_var, f"interval_{task_id}"
            )
            for res in task.resources:
                self.resources_usage[res].append(task.interval_var)

        # 2. Resource Constraints (No-Overlap)
        for intervals in self.resources_usage.values():
            self.model.AddNoOverlap(intervals)

        # 3. Dependencies
        for dep in self.dependencies:
            from_start, from_end = self._get_start_end_vars(dep["from"])
            to_start, to_end = self._get_start_end_vars(dep["to"])

            ctype = dep["type"]
            delay = dep["max_delay"]

            if ctype == "normal":
                self.model.Add(to_start >= from_end)
            elif ctype == "no_wait":
                self.model.Add(to_start == from_end)
            elif ctype == "grace_period":
                self.model.Add(to_start >= from_end)
                self.model.Add(to_start <= from_end + delay)
            elif ctype == "sync_ends":
                self.model.Add(to_end - from_end <= delay)
                self.model.Add(from_end - to_end <= delay)

        # 4. Objective: Minimize Makespan
        obj_var = self.model.NewIntVar(0, self.horizon, "makespan")
        self.model.AddMaxEquality(obj_var, [t.end_var for t in self.tasks.values()])
        self.model.Minimize(obj_var)

    def solve(self):
        """Solves the model and extracts the optimal schedule."""
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("No feasible schedule found. Constraints are too tight!")
            return

        print(
            f"Optimal Schedule Found! Total Time: {solver.ObjectiveValue()} minutes\n"
        )

        self.schedule_data = []

        # Sort tasks chronologically for clean terminal output
        solved_tasks = sorted(
            self.tasks.values(), key=lambda t: (solver.Value(t.start_var), t.name)
        )

        for task in solved_tasks:
            start_time = solver.Value(task.start_var)
            end_time = solver.Value(task.end_var)

            # Print to terminal
            print(
                f"Minute {start_time:02d} to {end_time:02d} | "
                f"{task.name} | Uses: {', '.join(task.resources)}"
            )

            # Save exploded resource data for plotting
            for res in task.resources:
                self.schedule_data.append(
                    {
                        "Task": task.name,
                        "Start": start_time,
                        "End": end_time,
                        "Duration": task.duration,
                        "Resource": res,
                    }
                )

    def plot_gantt(self, title: str = "Resource Utilization Timeline"):
        """Generates and opens a Resource Utilization chart in the browser."""
        if not self.schedule_data:
            print("No schedule data to plot. Please run solve() first.")
            return

        df = pd.DataFrame(self.schedule_data)
        df.sort_values(by=["Resource", "Start"], ascending=[True, True], inplace=True)

        fig = px.bar(
            df,
            x="Duration",
            y="Resource",
            base="Start",
            color="Task",
            orientation="h",
            title=title,
            hover_data=["Start", "End"],
            text="Task",
        )

        fig.update_layout(
            xaxis_title="Time (Minutes)",
            yaxis_title="Resources",
            showlegend=True,
            plot_bgcolor="rgba(240, 240, 240, 0.8)",
            barmode="overlay",
        )
        fig.update_traces(textposition="inside", insidetextanchor="middle")
        fig.show(renderer="browser")
