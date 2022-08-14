# -*- coding: utf-8 -*-

# import pickle
import cloudpickle  # needed to serialize Prefect workflow runs and tasks

from simmate.database.base_data_types import DatabaseTable, table_column

# BUG: I have this database table within a module that calls "database.connect"
# at a higher level... Will this cause circular import issues?


class WorkItem(DatabaseTable):
    # The name WorkItem comes from the naming convention use here:
    # https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py

    # For serialization, I just use the pickle module, but in the future, I may
    # want to do a priority of MsgPk >> JSON >> Pickle. I could check if the given
    # object(s) has a serialize() method, check if has a to_json() method, and then
    # as a last resort just pickle the object.
    # https://docs.python.org/3/library/pickle.html

    # Pickled objects are just written as byte strings, so I stored them in django
    # as a BinaryField which accepts bytes.
    # https://docs.djangoproject.com/en/3.1/ref/models/fields/#binaryfield

    # There is a repo that goes one step further and makes a PickleField for django
    # but this looks over the top for what I need -- even though django-picklefield
    # is only one file! Still, I can use it as a reference if I ever run into bugs
    # https://github.com/gintas/django-picklefield

    class Meta:
        app_label = "workflow_engine"

    tags = table_column.JSONField(default=[])
    """
    List of tags to submit the task with, which helps with submitting workers
    for a specific type of task/workflow. (e.g. ["simmate", "custom"])
    """

    fxn = table_column.BinaryField()
    """
    The function to be called, which is serialized into a binary format.
    """

    args = table_column.BinaryField(default=cloudpickle.dumps([]))
    """
    positional arguments to be passed into fxn
    """

    kwargs = table_column.BinaryField(default=cloudpickle.dumps({}))
    """
    keyword arguments to be passed into fxn
    """

    result = table_column.BinaryField(blank=True, null=True)
    """
    the output of fxn(*args, **kwargs)
    """

    command_not_found_failures = table_column.IntegerField(default=0)
    """
    Keeps track of the special-case "CommandNotFound" error that is hidden by
    workers. This keeps a tally of how many Workers that this task is triggering
    to shut down. This is important because it helps prevent total cluster
    shutdown from a single typo in a command. By default, workers will label
    a task as problematic if 2 workers give CommandNotFound errors.
    """

    source = None
    """
    Source column is not needed so setting this to None disables the column
    """

    # These states are based on the python queue module
    class StatusOptions(table_column.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        CANCELLED = "C"
        # CANCELLED_AND_NOTIFIED = "N"  # !!! when should I use this?
        FINISHED = "F"

    # TODO -- I should consider indexing this column for speed because it's
    # the most queried column by far.
    status = table_column.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )
    """
    the status/state of the workitem
    """

    # TODO: Consider creating a separate table for Worker and linking it to this
    # table via a foreign key.
    # worker_id = table_column.CharField(max_length=50, blank=True, null=True)
