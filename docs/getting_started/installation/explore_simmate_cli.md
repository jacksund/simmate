# Navigating Simmate's Command-Line Interface

Just as we used the `--help` flag with `uv` or `conda` earlier, we can also use it with Simmate. Try running:

``` bash
simmate --help
``` 

The following output should be displayed:

``` text                                                                                                       
 Usage: simmate [OPTIONS] COMMAND [ARGS]...                                                                     
                                                                                                                
 This is the base command that all other Simmate commands stem from 🔥🔥🚀                                                                                               
                                                                                                                
╭─ Options ──────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────╮
│ version        Prints the version of simmate that is installed.                            │
│ run-server     Runs a local test server for the Simmate website interface                  │
│ start-project  Creates a new folder and fills it with an example Simmate app               │
│ config         A group of commands for managing Simmate settings                           │
│ database       A group of commands for managing your database                              │
│ compute        A group of commands for starting up computational resources                 │
│                (Workers, Clusters, and Schedulers)                                         │
│ workflows      A group of commands for running workflows or viewing their settings         │
│ utils          A group of commands for various simple tasks (such as file handling)        │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

The output shows us that there are several command groups like `simmate database` and `simmate workflows` that we will explore in later tutorials. For instance, you can run `simmate database --help` to see all commands related to your database.
