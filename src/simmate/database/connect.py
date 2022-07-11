# -*- coding: utf-8 -*-

"""
This file connects to the Simmate database. Behind the scenes, this is really
setting up Django settings (which includes the database). Therefore, this 
file serves as a shortcut for the following:

``` python    
# the convenient shortcut
from simmate.database import connect

# the longer import that does the exact same thing
from simmate.configuration.django import setup
```
"""

# This import sets up Django so we can connect with the Simmate database
from simmate.configuration.django import setup
