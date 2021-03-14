# -*- coding: utf-8 -*-

"""
To prevent database-connection leaks, we want to setup django upfront when
a worker is started -- rather than have each task connect separately.
"""

from dask.distributed import WorkerPlugin


class DjangoPlugin(WorkerPlugin):
    def setup(self, worker):

        print("PRELOADING DJANGO TO DASK WORKER")

        # First setup django settings for simmate
        from simmate.configuration.django import setup_full  # ensures setup

        # The settings (including the database) are all set up now, but django doesn't
        # actually connect to the database until a query is made. So here, we do a
        # very simple query that should work for any django database. We don't actaully
        # need the output. We just want make a call that establishes a connection.
        # Let's just use the ContentType table because it's typically small.
        from django.contrib.contenttypes.models import ContentType

        # and make a quick query
        ContentType.objects.count()

    def teardown(self, worker):

        print("SHUTING DOWN DASK WORKER CONNECTIONS TO DJANGO WORKER")

        # grab all of the existing database connections for this thread
        from django.db import connections

        # close all of these connections to prevent connection leaking
        connections.close_all()


# def dask_setup(scheduler):
#     plugin = DjangoPlugin()
#     client.register_worker_plugin(plugin)  # doctest: +SKIP

# from simmate.configuration.dask.init_django_worker import DjangoPlugin
# plugin = DjangoPlugin()
# client.register_worker_plugin(plugin)
