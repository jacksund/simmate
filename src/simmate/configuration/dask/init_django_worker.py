# -*- coding: utf-8 -*-

"""
To prevent database-connection leaks, we want to setup django upfront when
a worker is started -- rather than have each task connect separately.

You can set this up with...
    from dask.distributed import Client
    client = Client(preload="simmate.configuration.dask.init_django_worker")
"""

# First setup django settings for simmate
from simmate.configuration.django import setup_full  # ensures setup

# BUG: do I want to make a connection first? It looks like if the connection
# closes at any point, then all following tasks will fail -- that is, once
# the connection closes, no following tasks reopen it. Maybe if I don't establish
# the connection upfront, I can just let every task make their own.
# The error I get is...
#   Unexpected error: InterfaceError('connection already closed') dask
# This has only happened when I submit >5,000 flow runs, so there may be too
# many connections opened at that point. I'm not sure if that's actually the
# case though.

# The settings (including the database) are all set up now, but django doesn't
# actually connect to the database until a query is made. So here, we do a
# very simple query that should work for any django database. We don't actaully
# need the output. We just want make a call that establishes a connection.
# Let's just use the ContentType table because it's typically small.
from django.contrib.contenttypes.models import ContentType

# and make a quick query
ContentType.objects.count()

# --------------------------------------------------------------------------------------

# THIS REPRESENTS A PLUGIN FOR A DASK WORKER. I MAY WANT TO SWITCH TO THIS APPROACH
# IN THE FUTURE. See here: https://distributed.dask.org/en/latest/plugins.html

# from dask.distributed import WorkerPlugin


# class DjangoPlugin(WorkerPlugin):
#     def setup(self, worker):

#         print("PRELOADING DJANGO TO DASK WORKER")

#         # First setup django settings for simmate
#         from simmate.configuration.django import setup_full  # ensures setup

#         # The settings (including the database) are all set up now, but django doesn't
#         # actually connect to the database until a query is made. So here, we do a
#         # very simple query that should work for any django database. We don't actaully
#         # need the output. We just want make a call that establishes a connection.
#         # Let's just use the ContentType table because it's typically small.
#         from django.contrib.contenttypes.models import ContentType

#         # and make a quick query
#         ContentType.objects.count()

#     def teardown(self, worker):

#         print("SHUTING DOWN DASK WORKER CONNECTIONS TO DJANGO WORKER")

#         # grab all of the existing database connections for this thread
#         from django.db import connections

#         # close all of these connections to prevent connection leaking
#         connections.close_all()


# REGISTER WITH....
# # def dask_setup(scheduler):
# #     plugin = DjangoPlugin()
# #     client.register_worker_plugin(plugin)  # doctest: +SKIP
# OR...
# from dask.distributed import Client
# client = Client(cluster.scheduler.address)
# from simmate.configuration.dask.init_django_worker import DjangoPlugin
# plugin = DjangoPlugin()
# client.register_worker_plugin(plugin)
