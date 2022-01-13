Simmate Calculators
--------------------

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

In a more logical order (rather than alphabetical like above), here is what each module contains:

- `configuration` = helps to install the program and setup common settings for it
- `inputs` & `outputs` = automatically generate files as well as load their data into python
- `error_handlers` = help correct common errors in calculations that cause the program to fail
- `tasks` = how the program is actually setup, executed, and worked-up. It ties together all the `inputs`, `outputs`, and `error-handler` functions into one. A single task can be viewed as a single call to the program (i.e. a single calculation).
- `database` = holds all of the datatables for storing our results
- `workflows`  = brings together `tasks` and `database`, so these setup individual tasks and handle saving the results to our database
- `website` = lets us submit workflows and view results with our website interface

**NOTE:** *Beginners should start by looking at the `workflows` module as this ties all other modules together. Advanced users can start with each calculator's `tasks` to build your own custom workflow.*
