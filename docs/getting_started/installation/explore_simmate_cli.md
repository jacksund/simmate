# Navigating Simmate's Command-Line Interface

Just as we used the `--help` flag with `uv` or `conda` earlier, we can also use it with Simmate. Try running:

``` bash
simmate --help
``` 

The following output should be displayed:

``` text                                                                                                       
                                                                                                                          
 Usage: simmate [OPTIONS] COMMAND [ARGS]...                                                                               
                                                                                                                          
 Simmate: A full-stack framework for chemistry research                                                            
                                                                                                                          
 This is the base command that all other Simmate commands stem from. For help with a specific command group, use simmate  
 <group> --help (e.g., simmate database --help).                                                                          
                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ compute    Commands for managing computational resources, including workers, clusters, and task scheduling.            │
│ config     Commands for managing Simmate settings, including viewing, updating, and testing app configurations.        │
│ database   Commands for managing the Simmate database, including Postgres setup, schema migrations, and data I/O.      │
│ desktop    Commands for launching and building the Simmate desktop app.                                                │
│ dev        Commands for Simmate development (linting, testing, docs, and cleanup).                                     │
│ init       Initializes a new Simmate project directory from a template.                                                │
│ version    Displays the currently installed version of Simmate and checks for updates.                                 │
│ website    Commands for running the Simmate Web UI.                                                                    │
│ workflows  Commands for exploring, configuring, and executing Simmate workflows.                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

The output shows us that there are several command groups like `simmate database` and `simmate workflows` that we will explore in later tutorials. For instance, you can run `simmate database --help` to see all commands related to your database.
