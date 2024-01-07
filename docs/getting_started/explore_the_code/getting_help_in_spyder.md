# Accessing Help in Spyder

----------------------------------------------------------------------

## Utilizing Auto-complete in Python

In our previous tutorial, we demonstrated how to display all available properties and methods for an object. This was achieved by typing the object name followed by a period (e.g., `nacl_structure.`) and then pressing `tab`:

```python
from simmate.toolkit import Structure

nacl_structure = Structure.from_file("POSCAR")

nacl_structure.  # press "tab" on your keyboard
```

!!! warning
    Please note that pymatgen's documentation may not always be comprehensive or beginner-friendly. This is why you might not see much information. At Simmate, we're working on improving this, so we hope to see enhancements in the future. For now, don't anticipate extensive guidance from the `Structure` class.

----------------------------------------------------------------------

## Locating a Method's Documentation

Let's now focus on obtaining comprehensive documentation for these methods and properties. We'll begin with the `Structure` class that we previously imported using `from simmate.toolkit import Structure` and try the command `Structure?`:

```python 
from simmate.toolkit import Structure

Structure?  # the "?" here will display the documentation
```

This command will bring up the documentation. Similar to how we used `--help` in the command-line in the first tutorial, we can use `?` in Python to access help for Python classes and objects!

We can also neatly format this documentation using Spyder. In the lower section of Spyder's top-right window, select the `help` tab. Then, in the adjacent search bar (labelled "object"), type in `Structure`. The help information will reappear, but this time it will be neatly formatted.

Let's apply this to our NaCl structure from earlier. Type `nacl_structure.get_primitive_structure` in the help window. You'll now see a description of this function and the arguments/options ("Args") it accepts.

You can also access this help information by typing `nacl_structure.get_primitive_structure` in the Python terminal and then using the `ctrl+I` shortcut.

```python
nacl_structure.get_primitive_structure  # press "ctrl+I" BEFORE hitting enter on this line
```

!!! tip
    If the documentation appears too brief or doesn't provide the information you need, we likely have more comprehensive guides in the "Full Guides & Reference" section.

----------------------------------------------------------------------