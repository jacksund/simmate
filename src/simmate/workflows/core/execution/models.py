
# --------------------------------------------------------------------------------------

import pickle

from django.db import models

# TYPES OF RELATIONSHIPS:
# ManyToMany - place in either but not both
# ManyToOne (ForeignKey) - place in the many
# OneToOne - place in the one that has extra features (it's like setting a parent class)

# --------------------------------------------------------------------------------------

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

# The name WorkItem comes from the naming convention use here:
# https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py

# --------------------------------------------------------------------------------------


class WorkItem(models.Model):

    """ Base info """

    # The function to be called
    fxn = models.BinaryField()

    # arguments to be passed into fxn
    args = models.BinaryField(default=pickle.dumps([]))

    # keyword arguments to be passed into fxn
    kwargs = models.BinaryField(default=pickle.dumps({}))

    # the output of fxn(*args, **kwargs)
    result = models.BinaryField(blank=True, null=True)

    # the status/state of the workitem
    # These states are based on the python queue module
    # TODO - Job canceling is not supported yet
    class StatusOptions(models.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        # CANCELLED = "C"
        # CANCELLED_AND_NOTIFIED = "N"
        FINISHED = "F"

    # TODO -- I should consider indexing this column for speed because it's
    # the most queried column by far.
    status = models.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )

    # the worker ID that grabbed the workitem
    worker_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        app_label = "execution"
