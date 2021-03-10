# -*- coding: utf-8 -*-

from simmate.configuration.django.setup import setup_full

# When I import this module, it automatically configures django for us, including
# connecting to the database(s). Without this file, I would instead need these two
#  lines in every single file before I import models:
#   from simmate.configuration.django.setup import setup_full
#   setup_full() # ensures setup
# With this init, I instead only need to have one line:
#   from simmate.configuration import django # ensures setup
setup_full()
