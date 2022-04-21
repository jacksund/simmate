# -*- coding: utf-8 -*-

"""
To prevent database-connection leaks, we want to setup django upfront when
a worker is started -- rather than have each task connect separately.

You can use this script like so...

``` python 
    from dask.distributed import Client
    client = Client(preload="simmate.configuration.dask.connect_to_database")
```

Note, there is also a high-level utility for this, which can be easier to
remember:
    
``` python
from simmate.utilities import get_dask_client
client = get_dask_client()
"""

# --------------------------------------------------------------------------------------


# First setup django settings for simmate
from simmate.database import connect

# The settings (including the database) are all set up now, but django doesn't
# actually connect to the database until a query is made. So here, we do a
# very simple query that should work for any django database. We don't actaully
# need the output. We just want make a call that establishes a connection.
# Let's just use the ContentType table because it's typically small.
from django.contrib.contenttypes.models import ContentType

# and make a quick query
ContentType.objects.count()


# --------------------------------------------------------------------------------------


# BUG: do I want to make a connection first? It looks like if the connection
# closes at any point, then all following tasks will fail -- that is, once
# the connection closes, no following tasks reopen it. Maybe if I don't establish
# the connection upfront, I can just let every task make their own.
# The error I get is...
#   Unexpected error: InterfaceError('connection already closed') dask
# This has only happened when I submit >5,000 flow runs, so there may be too
# many connections opened at that point. I'm not sure if that's actually the
# case though.

# BUG: for scaling Dask to many workers, I initially ran into issues of "too many
# files open". This is addressed in Dask's FAQ:
#   https://distributed.dask.org/en/latest/faq.html#too-many-open-file-descriptors
# To summarize the fix...
#   (1) check the current soft limit (soft = no sudo permissions) for  files
#       ulimit -Sn
#   (2) to increase the softlimit, edit the limits.conf file and add one line
#       sudo nano /etc/security/limits.conf
#           # add this line below
#           * soft nofile 10240
#   (3) close and reopen the terminal
#   (4) confirm we changed the limit
#       ulimit -Sn
#
# This may also be a leak of sockets being left open by Dask:
#   (1) get the PID of the running process with
#       ps -aef | grep python
#   (2) look at the fd's (file opened) by the given process
#       cd /proc/<PID>/fd; ls -l
#   (3) count the number of files opened by the given process
#       ls /proc/<PID>/fd/ | wc -l
#   (4) view overall stats with
#       cat /proc/<PID>/net/sockstat
#   (5) another option to list open files is
#       lsof -p <PID> | wc -l
#
# Whenever I see a heartbeat fail, I also see a massive jump in the number of
# files opened by the process. I believe zombie prefect runs are creating
# a socket leak.
#

# --------------------------------------------------------------------------------------

# THIS REPRESENTS A PLUGIN FOR A DASK WORKER. I MAY WANT TO SWITCH TO THIS APPROACH
# IN THE FUTURE. See here: https://distributed.dask.org/en/latest/plugins.html

# from dask.distributed import WorkerPlugin


# class DjangoPlugin(WorkerPlugin):
#     def setup(self, worker):

#         print("PRELOADING DJANGO TO DASK WORKER")

#         # First setup django settings for simmate
#         from simmate.database import connect  # ensures setup

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
# from simmate.configuration.dask.connect_to_database import DjangoPlugin
# plugin = DjangoPlugin()
# client.register_worker_plugin(plugin)
