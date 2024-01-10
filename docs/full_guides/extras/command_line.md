# The Simmate Command-line Interface

This module introduces the `simmate` command and its related sub-commands.

It's crucial to understand that most commands in this module serve as wrappers for more fundamental functions, which explains the minimal code here. For example, the `simmate database reset` command is merely a wrapper for the Python code below:

``` python
from simmate.database import connect
from simmate.database.utilities import reset_database

reset_database()
```

We've built our command-line using [Click](https://click.palletsprojects.com/en/8.0.x/) instead of Argparse. We recommend familiarizing yourself with Click's documentation before contributing to this module.

**WARNING**: We recommend using the command-line directly for interaction and usage, rather than referring to the online documentation provided here. This recommendation stems from our use of [typer](https://github.com/tiangolo/typer), which provides a more efficient overview of options compared to the API docs shown here.