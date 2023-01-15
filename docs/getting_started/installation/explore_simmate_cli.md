
# Exploring Simmate's command-line

Just like we used `conda --help` above, we can also ask for help with Simmate. Start with running the command `simmate --help` and you should see the following output:

``` shell
simmate --help
```

```                                                                                                           
 Usage: simmate [OPTIONS] COMMAND [ARGS]...                                                                     
                                                                                                                
 This is the base command that all other Simmate commands stem from 🔥🔥🚀                                      
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
 If you are a beginner to the command line, be sure to start with our tutorials. Below you will see a list of   
 sub-commands to try. For example, you can run simmate database --help to learn more about it.                  
                                                                                                                
 TIP: Many Simmate commands are long and verbose. You can use --install-completion to add ipython-like          
 autocomplete to your shell.                                                                                    
                                                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                      │
│ --show-completion             Show completion for the current shell, to copy it or customize the             │
│                               installation.                                                                  │
│ --help                        Show this message and exit.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────╮
│ database         A group of commands for managing your database                                              │
│ engine  A group of commands for starting up computational resources (Workers, Agents, and Clusters)          │
│ run-server       Runs a local test server for the Simmate website interface                                  │
│ start-project    Creates a new folder and fills it with an example project to get you started with custom    │
│                  Simmate workflows/datatables                                                                │
│ utilities        A group of commands for various simple tasks (such as file handling)                        │
│ workflows        A group of commands for running workflows or viewing their settings                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

You can see there are many other commands like `simmate database` and `simmate workflows` that we will explore in other tutorials. 
