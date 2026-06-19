# -*- coding: utf-8 -*-


class Task:
    """Represents a standard, continuous task."""

    def __init__(
        self,
        task_id: str,
        name: str,
        duration: int,
        resources: str | list[str],
    ):
        self.task_id = task_id
        self.name = name
        self.duration = duration
        self.resources = [resources] if isinstance(resources, str) else resources

        # Assigned during scheduling via cp_model
        self.start_var = None
        self.end_var = None
        self.interval_var = None


class PreemptableTask:
    """Represents a task that can be paused by splitting it into sequential chunks."""

    def __init__(
        self,
        task_id: str,
        name: str,
        total_duration: int,
        chunk_size: int,
        resources: str | list[str],
    ):
        self.task_id = task_id
        self.name = name
        self.resources = [resources] if isinstance(resources, str) else resources

        # Split the task into sequentially dependent standard Tasks
        num_chunks = total_duration // chunk_size
        self.chunks = [
            Task(f"{task_id}_{i+1}", f"{name} (Part {i+1})", chunk_size, self.resources)
            for i in range(num_chunks)
        ]
