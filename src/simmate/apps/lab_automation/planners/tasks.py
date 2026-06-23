# -*- coding: utf-8 -*-

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from ortools.sat.python import cp_model


class BaseTask(ABC):
    """Abstract base class for all schedulable tasks."""

    def __init__(
        self, name: str, resources: str | list[str], task_id: Optional[str] = None
    ):
        self.task_id = task_id or uuid.uuid4().hex[:8]
        self.name = name
        self.resources = [resources] if isinstance(resources, str) else resources

        # Assigned during scheduling via cp_model
        self.start_var = None
        self.end_var = None

    def __str__(self):
        return f"{self.name} ({self.task_id})"

    def __repr__(self):
        return f"<{self.__class__.__name__} id='{self.task_id}' name='{self.name}'>"

    @abstractmethod
    def update_horizon(self, current_horizon: int) -> int:
        pass

    @abstractmethod
    def update_min_time(self, current_min: int) -> int:
        pass

    @abstractmethod
    def build_variables(
        self,
        model: cp_model.CpModel,
        horizon: int,
        min_time: int,
        resources_usage: dict,
    ):
        pass

    @abstractmethod
    def get_penalty(self, model: cp_model.CpModel, horizon: int) -> Optional[object]:
        pass

    @abstractmethod
    def process_solution(self, solver: cp_model.CpSolver) -> list[dict]:
        pass


class Task(BaseTask):
    """Represents a standard, continuous task."""

    def __init__(
        self,
        name: str,
        duration: int,
        resources: str | list[str],
        task_id: Optional[str] = None,
    ):
        super().__init__(name, resources, task_id=task_id)
        self.duration = duration
        self.interval_var = None

    def update_horizon(self, current_horizon: int) -> int:
        return current_horizon + self.duration

    def update_min_time(self, current_min: int) -> int:
        return current_min

    def build_variables(
        self,
        model: cp_model.CpModel,
        horizon: int,
        min_time: int,
        resources_usage: dict,
    ):
        self.start_var = model.NewIntVar(0, horizon, f"start_{self.task_id}")
        self.end_var = model.NewIntVar(0, horizon, f"end_{self.task_id}")
        self.interval_var = model.NewIntervalVar(
            self.start_var, self.duration, self.end_var, f"interval_{self.task_id}"
        )
        for res in self.resources:
            resources_usage[res].append(self.interval_var)

    def get_penalty(self, model: cp_model.CpModel, horizon: int) -> Optional[object]:
        return None

    def process_solution(self, solver: cp_model.CpSolver) -> list[dict]:
        start_time = solver.Value(self.start_var)
        end_time = solver.Value(self.end_var)

        print(
            f"Minute {start_time:02d} to {end_time:02d} | "
            f"{self.name} | Uses: {', '.join(self.resources)}"
        )

        return [
            {
                "Task": self.name,
                "Start": start_time,
                "End": end_time,
                "Duration": self.duration,
                "Resource": res,
            }
            for res in self.resources
        ]


class FixedTask(Task):
    """Represents a task that is pinned to a specific start and end time.
    Useful for resource downtime or tasks that are already ongoing."""

    def __init__(
        self,
        name: str,
        duration: int,
        start_time: int,
        resources: str | list[str],
        task_id: Optional[str] = None,
    ):
        super().__init__(name, duration, resources, task_id=task_id)
        self.start_time = start_time

    def update_horizon(self, current_horizon: int) -> int:
        return max(current_horizon + self.duration, self.start_time + self.duration)

    def update_min_time(self, current_min: int) -> int:
        return min(current_min, self.start_time)

    def build_variables(
        self,
        model: cp_model.CpModel,
        horizon: int,
        min_time: int,
        resources_usage: dict,
    ):
        self.start_var = model.NewIntVar(min_time, horizon, f"start_{self.task_id}")
        self.end_var = model.NewIntVar(min_time, horizon, f"end_{self.task_id}")
        self.interval_var = model.NewIntervalVar(
            self.start_var, self.duration, self.end_var, f"interval_{self.task_id}"
        )
        model.Add(self.start_var == self.start_time)
        model.Add(self.end_var == self.start_time + self.duration)
        for res in self.resources:
            resources_usage[res].append(self.interval_var)


class PreemptableTask(BaseTask):
    """Represents a task that can be paused by splitting it into sequential chunks."""

    def __init__(
        self,
        name: str,
        total_duration: int,
        min_chunk_size: int,
        max_chunks: int,
        resources: str | list[str],
        task_id: Optional[str] = None,
    ):
        super().__init__(name, resources, task_id=task_id)
        self.total_duration = total_duration
        self.min_chunk_size = min_chunk_size
        self.max_chunks = max_chunks

        # Assigned during scheduling via cp_model
        self.chunk_presences = []
        self.chunk_sizes = []
        self.chunk_starts = []
        self.chunk_ends = []
        self.chunk_intervals = []

    def update_horizon(self, current_horizon: int) -> int:
        return current_horizon + self.total_duration

    def update_min_time(self, current_min: int) -> int:
        return current_min

    def build_variables(
        self,
        model: cp_model.CpModel,
        horizon: int,
        min_time: int,
        resources_usage: dict,
    ):
        self.start_var = model.NewIntVar(0, horizon, f"start_{self.task_id}")
        self.end_var = model.NewIntVar(0, horizon, f"end_{self.task_id}")

        for i in range(self.max_chunks):
            is_present = model.NewBoolVar(f"present_{self.task_id}_{i}")
            size = model.NewIntVar(0, self.total_duration, f"size_{self.task_id}_{i}")
            start = model.NewIntVar(0, horizon, f"start_{self.task_id}_{i}")
            end = model.NewIntVar(0, horizon, f"end_{self.task_id}_{i}")

            interval = model.NewOptionalIntervalVar(
                start, size, end, is_present, f"interval_{self.task_id}_{i}"
            )

            self.chunk_presences.append(is_present)
            self.chunk_sizes.append(size)
            self.chunk_starts.append(start)
            self.chunk_ends.append(end)
            self.chunk_intervals.append(interval)

            for res in self.resources:
                resources_usage[res].append(interval)

            model.Add(size >= self.min_chunk_size).OnlyEnforceIf(is_present)
            model.Add(size == 0).OnlyEnforceIf(is_present.Not())

            if i > 0:
                model.AddImplication(is_present, self.chunk_presences[i - 1])
                model.Add(start >= self.chunk_ends[i - 1]).OnlyEnforceIf(is_present)

        model.Add(sum(self.chunk_sizes) == self.total_duration)
        model.Add(self.start_var == self.chunk_starts[0])
        model.AddMaxEquality(self.end_var, self.chunk_ends)

    def get_penalty(self, model: cp_model.CpModel, horizon: int) -> Optional[object]:
        span = model.NewIntVar(0, horizon, f"span_{self.task_id}")
        model.Add(span == self.end_var - self.start_var)
        return span

    def process_solution(self, solver: cp_model.CpSolver) -> list[dict]:
        active_chunks = []
        for i in range(self.max_chunks):
            if solver.BooleanValue(self.chunk_presences[i]):
                active_chunks.append(
                    {
                        "start": solver.Value(self.chunk_starts[i]),
                        "end": solver.Value(self.chunk_ends[i]),
                    }
                )

        if not active_chunks:
            return []

        merged_chunks = []
        current_chunk = active_chunks[0].copy()
        for i in range(1, len(active_chunks)):
            next_chunk = active_chunks[i]
            if current_chunk["end"] == next_chunk["start"]:
                current_chunk["end"] = next_chunk["end"]
            else:
                merged_chunks.append(current_chunk)
                current_chunk = next_chunk.copy()
        merged_chunks.append(current_chunk)

        schedule_data = []
        for j, chunk in enumerate(merged_chunks):
            start_time = chunk["start"]
            end_time = chunk["end"]
            chunk_size = end_time - start_time
            name = f"{self.name} (Part {j+1})" if len(merged_chunks) > 1 else self.name

            print(
                f"Minute {start_time:02d} to {end_time:02d} | "
                f"{name} | Uses: {', '.join(self.resources)}"
            )
            for res in self.resources:
                schedule_data.append(
                    {
                        "Task": name,
                        "Start": start_time,
                        "End": end_time,
                        "Duration": chunk_size,
                        "Resource": res,
                    }
                )
        return schedule_data
