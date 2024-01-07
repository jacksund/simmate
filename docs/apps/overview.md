## Understanding Apps

Apps are essentially codes or programs designed to perform specific analyses. They can be based on external software or custom-built using Simmate for a particular technique.

For instance, VASP is a program capable of running a variety of density functional theory (DFT) calculations. However, since it's not written in Python, we require some "helper" code to execute VASP commands, create input files, and extract data from the outputs.

Similarly, Simmate includes an `evo_search` "app" that encompasses all the functionalities required to execute the evolutionary structure prediction algorithm.

## Code Structure

All apps adhere to the same folder structure:

```
├── example_app
│   ├── database
│   ├── error_handlers
│   ├── inputs
│   ├── outputs
│   ├── configuration
│   ├── tasks
│   ├── website
│   └── workflows
```

Here's a logical breakdown of what each module contains:

- `configuration`: Assists in installing the program and configuring common settings.
- `inputs` & `outputs`: Automates file generation and data loading into Python.
- `error_handlers`: Helps rectify common calculation errors that cause the program to fail.
- `tasks`: Defines how the program is set up, executed, and processed. It integrates all the `inputs`, `outputs`, and `error-handler` functions. A single task can be seen as a single call to the program (i.e., a single calculation).
- `database`: Contains all the datatables for storing our results.
- `workflows`: Combines `tasks` and `database` to set up individual tasks and manage the saving of results to our database.
- `website`: Allows us to submit workflows and view results via our website interface.

!!! note
    Beginners are advised to start with the `workflows` module as it integrates all other modules.