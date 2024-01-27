## Understanding Apps

Apps are groups of functionality designed to help with a specific analysis or third-party software.

For instance, VASP is a program capable of running a variety of density functional theory (DFT) calculations. However, since it's not written in Python, we require some "helper" code to execute VASP commands, create input files, and extract data from the outputs. This helper code is what makes up Simmate's `vasp` app.

Similarly, Simmate includes an `evolution` app that encompasses all the functionalities required to run evolutionary structure prediction.

## Source code for each app

All apps adhere to the same folder structure (though each folder is optional):

```
├── example_app
│   ├── configuration
│   ├── inputs
│   ├── outputs
│   ├── error_handlers
│   ├── models (aka database tables)
│   ├── website
│   └── workflows
```

Here's a logical breakdown of what each module contains:

- `configuration`: Assists in installing the program and configuring common settings.
- `inputs` & `outputs`: Automates file generation and data loading into Python.
- `error_handlers`: Helps rectify common calculation errors that cause the program to fail.
- `database`: Contains all the datatables for storing our results.
- `workflows`: Defines how the program is set up, executed, and processed by integrating all the `inputs`, `outputs`, and `error-handler` functions. Some workflows also use `database` and manage the saving of results.
- `website`: Inclides any website interface features the app may need.
