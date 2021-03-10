# -*- coding: utf-8 -*-

"""
To prevent database-connection leaks, we want to setup django upfront when
a worker is started -- rather than have each task connect separately.
"""

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
