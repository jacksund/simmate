# -*- coding: utf-8 -*-

"""
This module provides a single endpoint where all registered workflows can be
accessed for user-convenience. 

This is best for accessing workflows in a quick debugging manner. If you need
to access all workflows, we recommend using this utility instead:
``` python
simmate.workflows.utilities import get_all_workflows 
```
"""

# note, everything starts with an underscore because I don't want these variables
# to be visable -- only the workflow classes.
# The code below is modified from...
#   https://stackoverflow.com/questions/30986470/

from simmate.workflows.utilities import get_all_workflows as _get_all

_workflows = _get_all()
_module = globals()

for _workflow in _workflows:
    _module[_workflow.__name__] = _workflow
