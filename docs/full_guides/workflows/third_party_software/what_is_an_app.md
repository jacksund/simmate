
----------------------------------------------------------------------

## What is an app?

Apps are codes/programs that perform some analysis for us. They can be based an external software or even a custom program built using Simmate for a specific technique.

For example, VASP is a program that can run a variety of density functional theory (DFT) calculations. But because it isn't written in Python, we need some "helper" code here to call VASP commands, make input files, and pull data from the outputs.

As another example, Simmate includes a suite for evolutionary structure prediction. All of the functionality need to carry out the search algorithm is contained within an `evo_search` "app".

----------------------------------------------------------------------

## Organization of code

All apps follow the same folder structure:

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

In a more logical order (rather than alphabetical like above), here is what each module contains:

- `configuration` = helps to install the program and set up common settings for it
- `inputs` & `outputs` = automatically generate files as well as load their data into python
- `error_handlers` = help correct common errors in calculations that cause the program to fail
- `tasks` = how the program is actually set up, executed, and worked-up. It ties together all the `inputs`, `outputs`, and `error-handler` functions into one. A single task can be viewed as a single call to the program (i.e. a single calculation).
- `database` = holds all of the datatables for storing our results
- `workflows`  = brings together `tasks` and `database`, so these setup individual tasks and handle saving the results to our database
- `website` = lets us submit workflows and view results with our website interface

!!! note
    Beginners should start by looking at the `workflows` module as this ties all other modules together.

----------------------------------------------------------------------
