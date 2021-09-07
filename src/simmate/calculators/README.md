Calculators are external codes/programs that perform some analysis for us. 

For example, VASP is a program that can run a variety of density functional theory (DFT) calculations. But because it isn't written in Python, we need some "helper" code here to help us call VASP commands, make input files, and pull data from the outputs. All calculators have the same folder structure:
```
├── my_calculator
│   ├── error_handlers
│   ├── inputs
│   ├── outputs
│   └── tasks
```

The `inputs` and `outputs` folders are for automatically generating files as well as loading their data into python.

The `error_handlers` folder helps correct common errors in calculations that cause the program to fail.

The `tasks` folder is how the program is actually setup, executed, and worked-up. It ties together all the input, output, and error-handler functions into one.

**NOTE:** *Beginners should instead start by looking at the `simmate.workflows` module. This module should only be used directly if you're writing a brand new workflow or analysis. Otherwise, you can start with each calculator's `tasks` to build your own workflow.*
