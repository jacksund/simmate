
# A quick introduction to python terms

As you read through our tutorials, we try to explain many of the python terms and concepts, but for your reference, we have written out some quick definitions here. You won't be expected to understand all of these terms until tutorial 06, so revisit these definitions after each tutorial to review your understanding.

- `package`: A package is, essentially, a program written in python. Simmate is a package.
- `package manager`: A package manager is what installs Python and any extra packages for us. Importantly, it makes sure we install the correct version of Python and packages. Anaconda is our package manager, and it installs Python and Simmate for us.
- `environment`: python packages are installed into a specific environment on your computer. An environment is (effectively) a folder containing many installed packages that are each compatible each other. A single computer can have many environments, where you only ever use one at a time.  In this tutorial, "my_env" is the name of our environment and Simmate is installed in it (along with many other packages such as pymatgen and numpy).
- `module`: A python package is made from modules.  Each module provides a related set of functions. For example, "simmate.database" is a module that holds all of the code used to run our database.
- `IDE`: the program we write and run python code in. Microsoft Word would be an IDE for writing essays. Spyder is our IDE for python. IDE is short for integrated development environment.

Also, don't confuse two types of programming language we will use:

- `command-line`: Whether you are on Windows, Mac, or Linux, the command line (aka the terminal) is used for common functions like changing directories (cd Desktop) or running programs. This includes running python modules, such as: "simmate workflows run".
- `python`: used when we write complex logic and customize its settings. "workflow.run(structure=...)" is python code used in our IDE.

