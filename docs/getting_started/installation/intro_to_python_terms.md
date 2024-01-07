# A Quick Guide to Python Terminology

In our tutorials, we aim to clarify various Python terms and concepts. However, we've also compiled a quick reference guide here for your convenience. Don't worry if you don't grasp all these terms immediately - you're not expected to fully understand them until tutorial 06. Feel free to revisit these definitions after each tutorial to reinforce your understanding.

----------------------------------------------------------------------

## Package
In simple terms, a package is a program written in Python. For instance, Simmate is a package.

----------------------------------------------------------------------

## Package Manager
A package manager is a tool that installs Python and any additional packages for us. Crucially, it ensures we install the correct versions of Python and packages. Anaconda is our package manager of choice, responsible for installing Python and Simmate.

----------------------------------------------------------------------

## Environment
Python packages are installed into a specific environment on your computer. Essentially, an environment is a folder containing numerous installed packages that are compatible with each other. A single computer can host multiple environments, but you'll only ever use one at a time. In this tutorial, "my_env" is our environment, and it houses Simmate along with other packages like pymatgen and numpy.

----------------------------------------------------------------------

## Module
A Python package is composed of modules. Each module offers a related set of functions. For instance, "simmate.database" is a module containing all the code required to operate our database.

----------------------------------------------------------------------

## IDE
IDE, or Integrated Development Environment, is the software where we write and execute Python code. Microsoft Word would be an IDE for writing essays. Spyder is our IDE for python.

----------------------------------------------------------------------

## Command Line vs. Python
It's important not to mix up the two types of programming languages we'll be using:

- `command-line`: Regardless of whether you're using Windows, Mac, or Linux, the command line (also known as the terminal) is used for basic functions like changing directories (`cd Desktop`) or running programs. This includes executing commands like `simmate workflows run`.
- `python`: This is used when we need to write complex logic and customize settings. `workflow.run(structure=...)` is an example of Python code used in our IDE.

----------------------------------------------------------------------