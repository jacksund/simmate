Calculators are external codes/programs that perform some analysis for us. 

For example, VASP is a program that can run a variety of density functional theory (DFT) calculations. But because it isn't written in Python, we need some "helper" code here to call VASP commands, make input files, and pull data from the outputs. 

All calculators have the same folder structure:
```
├── example_calculator
│   ├── database
│   ├── error_handlers
│   ├── inputs
│   ├── outputs
│   ├── configuration
│   ├── tasks
│   ├── website
│   └── workflows
```

**NOTE:** *Beginners should start by looking at the `workflows` module as this ties all other modules together. Advanced users can start with each calculator's `tasks` to build your own custom workflow.*

In a more logical order (rather than alphabetical like above), here is what each module contains:

The `configuration` module helps to install the program and setup common settings for it.

The `inputs` and `outputs` are for automatically generating files as well as loading their data into python.

The `error_handlers` help correct common errors in calculations that cause the program to fail.

The `tasks` are how the program is actually setup, executed, and worked-up. It ties together all the `inputs`, `outputs`, and `error-handler` functions into one. A single task can be viewed as a single call to the program (i.e. a single calculation).

The `database` holds all of the datatables for storing our results.

The `workflows` bring together `tasks` and `database` -- so these setup individual tasks and handle saving the results to our database.

The `website` module is for letting us submit workflows and view results with our website interface.
