# -*- coding: utf-8 -*-

import collections

import pandas as pd
import plotly.express as px
from ortools.sat.python import cp_model

from simmate.apps.lab_automation.planners.tasks import BaseTask


class SchedulePlanner:
    """Plans and optimizes task execution timelines using OR-Tools."""

    def __init__(self):
        self.model = cp_model.CpModel()
        self.tasks: dict[str, BaseTask] = {}
        self.dependencies: list[dict] = []
        self.resources_usage = collections.defaultdict(list)
        self.horizon: int = 0
        self.schedule_data: list[dict] = []

    def add_task(self, task: BaseTask) -> BaseTask:
        self.tasks[task.task_id] = task
        self.horizon = task.update_horizon(self.horizon)
        return task

    def add_tasks(self, *tasks: BaseTask | list[BaseTask]):
        if len(tasks) == 1 and isinstance(tasks[0], (list, tuple)):
            tasks = tasks[0]
        for task in tasks:
            self.add_task(task)
        return tasks

    def add_dependency(
        self,
        from_task: str | BaseTask,
        to_task: str | BaseTask,
        constraint_type: str = "normal",
        max_delay: int = 0,
    ):
        from_id = from_task.task_id if isinstance(from_task, BaseTask) else from_task
        to_id = to_task.task_id if isinstance(to_task, BaseTask) else to_task
        self.dependencies.append(
            {
                "from": from_id,
                "to": to_id,
                "type": constraint_type,
                "max_delay": max_delay,
            }
        )

    def add_chain(
        self,
        *tasks: str | BaseTask | list[str | BaseTask],
        constraint_type: str = "normal",
        max_delay: int = 0,
    ):
        """Adds a sequential chain of dependencies between tasks."""
        if len(tasks) == 1 and isinstance(tasks[0], (list, tuple)):
            tasks = tasks[0]
        for i in range(len(tasks) - 1):
            self.add_dependency(
                tasks[i],
                tasks[i + 1],
                constraint_type=constraint_type,
                max_delay=max_delay,
            )

    def _get_start_end_vars(self, task_id: str) -> tuple:
        """Helper to retrieve start/end OR-Tools variables for a given task ID."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return task.start_var, task.end_var
        raise ValueError(f"Task ID '{task_id}' not found in scheduler!")

    def build_model(self):
        """Initializes CP variables, resource constraints, and temporal dependencies."""
        # 1. Variables and Resource Mapping
        min_time = 0
        for task in self.tasks.values():
            min_time = task.update_min_time(min_time)

        for task in self.tasks.values():
            task.build_variables(
                self.model, self.horizon, min_time, self.resources_usage
            )

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

        # 4. Objective: Minimize Makespan + Context Switch Penalty
        self.makespan_var = self.model.NewIntVar(min_time, self.horizon, "makespan")
        self.model.AddMaxEquality(
            self.makespan_var, [t.end_var for t in self.tasks.values()]
        )

        # Add penalty for preemptable tasks to minimize context switching
        # We minimize the total span (end - start) of preemptable tasks
        # multiplied by a small weight, prioritizing makespan over fragmentation.
        penalties = []
        for task in self.tasks.values():
            penalty = task.get_penalty(self.model, self.horizon)
            if penalty is not None:
                penalties.append(penalty)

        if penalties:
            self.model.Minimize(self.makespan_var * 100 + sum(penalties))
        else:
            self.model.Minimize(self.makespan_var)

    def solve(self):
        """Solves the model and extracts the optimal schedule."""
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("No feasible schedule found. Constraints are too tight!")
            return

        print(
            f"Optimal Schedule Found! Total Time: {solver.Value(self.makespan_var)} minutes\n"
        )

        self.schedule_data = []

        # Sort tasks chronologically for clean terminal output
        solved_tasks = sorted(
            self.tasks.values(), key=lambda t: (solver.Value(t.start_var), t.name)
        )

        for task in solved_tasks:
            schedule_dicts = task.process_solution(solver)
            self.schedule_data.extend(schedule_dicts)

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
            showlegend=False,
            plot_bgcolor="rgba(240, 240, 240, 0.8)",
            barmode="overlay",
        )
        fig.update_traces(textposition="inside", insidetextanchor="middle")
        fig.show(renderer="browser")
