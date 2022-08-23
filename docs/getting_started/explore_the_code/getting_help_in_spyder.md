
# Getting help through Spyder

Where we left off in Tutorial 3, we saw how to list all available properties and methods on an object. We did this by typing the object name plus a period (ex: `nacl_structure.`) and then hitting `tab`:

```python
from simmate.toolkit import Structure

nacl_structure = Structure.from_file("POSCAR")

nacl_structure.  # hit "tab" on your keyboard
```

> :warning: for this next part, pymatgen's documentation isn't always complete or beginner-friendly. This is why you won't see much. We're working on this at Simmate, so we hope this improves in the future. For now, don't expect too much guidance from the `Structure` class.

Now let's take a step back and get a full guide on a these methods and properties. We'll start with the `Structure` class that we previously imported using `from simmate.toolkit import Structure` and try the line `Structure?`:

```python 
from simmate.toolkit import Structure

Structure?  # <-- the ? here will bring up documentation help
```

What pops up is the documentation. Just like how we were using `--help` in the command-line for tutorial 1, we can use `?` in python to get help with python classes and objects!

We can also format this nicely using Spyder. In bottom part of Spyder's top-right window, select the `help` tab. And in the search bar (with "object") right next to it, type in `Structure`. You'll see the help information pop up again, but now it's nicely formatted for us.

Let's try this with our NaCl structure from before. Now try typing `nacl_structure.get_primitive_structure` in our help window. We can now see a description of what this does and the arguments/options ("Args") that it accepts.

You can also get this help information by typing `nacl_structure.get_primitive_structure` in the python terminal and then using the `ctrl+I` shortcut.

```python
nacl_structure.get_primitive_structure  # hit "ctrl+I" BEFORE hitting enter on this line
```
