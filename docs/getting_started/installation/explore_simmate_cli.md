# Navigating Simmate's Command-Line Interface

Just as we used `conda --help` earlier, we can also use `--help` with Simmate. Begin by running the command:

``` bash
simmate --help
``` 

The following output should be displayed:

```                                                                                                       
 Usage: simmate [OPTIONS] COMMAND [ARGS]...                                                                     
                                                                                                                
 This is the primary command from which all other Simmate commands originate. If you're new to the command line, we recommend starting with our tutorials. Below, you'll find a list of sub-commands to try. For instance, you can run `simmate database --help` to learn more about it.                  
                                                                                                                
 TIP: Many Simmate commands are lengthy and verbose. You can use --install-completion to add ipython-like autocomplete to your shell.                                                                                    
                                                                                                                
Options:
--install-completion          Install completion for the current shell.                                      
--show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                  
--help                        Show this message and exit.                                                    

Commands:
database         A group of commands for managing your database                                              
engine           A group of commands for starting up computational resources (Workers, Agents, and Clusters)          
run-server       Runs a local test server for the Simmate website interface                                  
start-project    Creates a new folder and fills it with an example project to get you started with custom Simmate workflows/datatables                                                                
utilities        A group of commands for various simple tasks (such as file handling)                        
workflows        A group of commands for running workflows or viewing their settings                         
```

As you can see, there are numerous other commands like `simmate database` and `simmate workflows` that we will delve into in later tutorials.