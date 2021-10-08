# Exploring our documentation and code on github

## The quick version

Simmate is not like other python packages because we want users to go through our code! We also put our documentation in READMEs that are directly in the python modules -- rather than having it on a separate webpage. We believe this prevents the "black-box" nature of codes and helps beginners understand how Simmate actually works. This tutorial slimply has you explore workflows while getting a feel for where our advanced tutorials/documentation is located.

> :warning: if you really prefer documentation made by Sphinx, we still offer it (via [pdoc](https://pdoc.dev/)

1. All of Simmate workflows can be found in the `simmate.workflows` module. To view what is available, you can use the spyder console's `tab` feature (from the last tutorial) to list them. From here, you can navigate to workflows like `simmate.workflows.relaxation.mit`. So to import this workflow and then run it, you'd use...
```python
# Load the structure file you'd like to use
from simmate.toolkit import Structure
my_structure = Structure.from_file('NaCl.cif')

# Load your workflow. Here we are loading a VASP Relaxation at MIT Project settings.
from simmate.workflows.relaxation.mit import workflow
result = workflow.run(structure=my_structure)
```
2. Finding workflows entirely through the python console can be challenging and slow. It also doesn't show us what the workflow is doing. We therefore want users to explore these files themselves! Let's take the same workflow from step 1 and try to find it on github. To get there, we start on our [homepage](https://github.com/jacksund/simmate/tree/main) and select the folders `src/simmate` --> `workflows` --> `relaxation` --> `mit.py`. In it, we can see the workflow code!
3. 

So why did we have to go on this wild goose chase to find the code?

## The full tutorial

This tutorial will include...
- todo
