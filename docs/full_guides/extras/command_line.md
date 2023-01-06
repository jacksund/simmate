The Simmate Command-line Interface
----------------------------------

This module defines the `simmate` command and all of its sub-commands.

Note, nearly all of the commands in this module wrap a lower-level function, so little code is located here. For example, the `simmate database reset` command is just a wrapper for the following python code:

``` python
from simmate.database import connect
from simmate.database.utilities import reset_database

reset_database()
```

Our command-line is build using [Click](https://click.palletsprojects.com/en/8.0.x/) instead of Argparse. Be sure to read their documentation before contributing to this module.

**WARNING**: for interacting with and using the command-line, we recommend using it directly, rather than exploring online documentation here. This is because we use [typer](https://github.com/tiangolo/typer), which makes reading through options much cleaner than the api docs shown here.
