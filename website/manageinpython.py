
#############################################################################
### The code below is the equiv of running 'python manage.py shell'
#############################################################################

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings')

import django
django.setup()

del django
del os

#############################################################################
### Now you can import apps from your project and run any django commands
### Just include "import manageinpython" at the start of your script
#############################################################################
