# Exploring our documentation and code on github

## The quick version

> :warning: There is not a "quick-version" for this tutorial. For advanced users, you simply need to know that we have README.md files in each of our python modules. This is how we prefer to document our code -- rather than sphnix. This is because we are a high-level code and want to avoid researchers using it as a black-box software. Having docs right next to our code helps us keep our guides up-to-date too.

## The full tutorial

Simmate is not like other python packages because we want users to go through our code! We also put our documentation in READMEs directly in the python modules -- rather than having it on a separate webpage. We believe this prevents the "black-box" nature of codes and helps beginners understand how Simmate actually works. This tutorial slimply has you explore workflows while getting a feel for where our advanced tutorials/documentation is located.

> :warning: if you really prefer documentation made by Sphinx, we still offer it (via [pdoc](https://pdoc.dev/)) but don't update tutorials here.

1. All of Simmate workflows can be found in the `simmate.workflows` module. To view what is available, you can use the spyder console's `tab` feature (from the last tutorial) to list them. From here, you can navigate to workflows like `simmate.workflows.relaxation.mit`. So to import this workflow and then run it, you'd use...
```python
# Load the structure file you'd like to use
from simmate.toolkit import Structure
my_structure = Structure.from_file('NaCl.cif')

# Load your workflow. Here we are loading a VASP Relaxation at MIT Project settings.
from simmate.workflows.relaxation.mit import workflow
result = workflow.run(structure=my_structure)
```
2. Finding workflows entirely through the python console can be challenging. It doesn't answer key questions like "_how do I know what import path to use?_" or "_what is this workflow actually doing?_". We therefore want users to explore these files themselves! Let's take the same workflow from step 1 and try to find it on github. To get there, we start on our [homepage](https://github.com/jacksund/simmate/tree/main) and select the folders `src/simmate` --> `workflows` --> `relaxation` --> `mit.py`. In it, we can see the workflow code!
3. Let's backtrack a bit and go through these folders again. In each, you'll see a `README.md` file. This file is what's shown on github when you have the folder open. These describe everything you need to know about the folder you're in! So when searching for files and functions, be sure to read these for help. In the `src/simmate/workflows` folder for example, we can see an overview of all the workflows available as well as a quick guide on how to run workflows. Likewise, the `src/simmate/workflows/relaxation` folder tells us exactly what relaxations are doing and how to run them.
4. The workflow code shows that there are tasks and other functions being used, and we want to figure what they do too! To jump to this code, we can use the import path at the top of the file to find those functions. Let's use this line: 
```python
from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask
```
5. This is a really long path, but remember these are just a bunch of folders that lead to a file with the code for `MITRelaxationTask`. When we move to this file (again, explore the README's on your way!), we see `MITRelaxationTask` has all of the settings used to run our relaxation with VASP. The INCAR settings should be super clear to VASP users and also give begineers a place to understand how to run VASP.

6. Keep exploring Simmate and all of it modules! Explore the `simmate.calculators.vasp` module to get a feel for how we build off of other programs. Then jump to `simmate.toolkit` to explore simple functions you'll need to make new workflows or analyze your structures!
