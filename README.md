<!-- This displays the Simmate Logo -->
<p align="center" href=https://simmate.org>
   <img src="https://github.com/jacksund/simmate/blob/main/src/simmate/website/static_files/images/simmate-logo.svg?raw=true" width="700" style="max-width: 700px;">
</p>

<!-- This displays the dynamic badges -->
<p align="center">
<!-- Conda-forge OS support -->
<a href="https://anaconda.org/conda-forge/simmate">
    <img src="https://img.shields.io/badge/-Windows | Mac | Linux-043344">
</a>
<!-- Pricing statement for begineers that are new to github -->
<a href="https://anaconda.org/conda-forge/simmate">
    <img src="https://img.shields.io/badge/-Free & Open Source-043344">
</a>
<!-- link to JOSS paper -->
<a href="https://doi.org/10.21105/joss.04364">
    <img src="https://img.shields.io/badge/-DOI:10.21105/joss.04364-043344">
</a>

</br>
<!-- Link to API documentation -->
<a href="https://jacksund.github.io/simmate/simmate.html">
    <img src="https://img.shields.io/badge/-API docs-/?logo=microsoft-academic&color=043344&logoColor=white">
</a>
<!-- Link to Tutorials -->
<a href="https://github.com/jacksund/simmate/tree/main/tutorials">
    <img src="https://img.shields.io/badge/-Tutorials-/?logo=gitbook&color=043344&logoColor=white">
</a>
<!-- Link to Website -->
<a href="https://simmate.org/">
    <img src="https://img.shields.io/badge/-Website-/?logo=iCloud&color=043344&logoColor=white">
</a>
<!-- link to change-log -->
<a href="https://github.com/jacksund/simmate/blob/main/CHANGELOG.md">
    <img src="https://img.shields.io/badge/-Changes & Updates-/?logo=git-extensions&color=043344&logoColor=white">
</a>
</p>


<!-- 
I use html format above to center the objects. Otherwise I could simple markdown like this:
![Simmate Logo](https://github.com/jacksund/simmate/blob/main/logo/simmate.svg?raw=true)
Read here for info on markdown, badges, and more:
[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
[Shields Badges](https://shields.io/)
-->

> :warning: For Simmate's workflow module, we are currently reliant on VASP, which is an expensive DFT software that can be difficult to install for beginners. We are working to move away from propriatary softwares and toward free/open-source codes like ABINIT, Quantum Espresso, or DFTK.jl. That way you can install Simmate and we will take care of the rest. This will take time though... so we recommend that fully experimental labs wait until Simmate hits this milestone. If you'd like to be notified when this occurs, send us an email at simmate.team@gmail.com.

## Welcome!

If you are new to Simmate, jump over to our main website [simmate.org](https://simmate.org/) and take a look at what we have to offer. This page is for when you're ready to use Simmate in your own research and access some advanced functionality. Our software is open-source and free to use, so come back to try it when you're ready!


## What is Simmate?

The Simulated Materials Ecosystem (Simmate) is a toolbox and framework for computational materials research. It lets you explore various crystal databases, predict new materials, and quickly calculate properties (electronic, elastic, thermodynamic, and more).

Computational research can be intimidating because there are so many programs to choose from, and it's hard to mix-and-match them for your specific project. Simmate aims to be the glue between all these different programs, databases, and utilities. We do the heavy lifting and explain these other programs to you along the way.

Even if you consider yourself an experimentalist and have little-to-no coding experience, Simmate's barrier to entry is built to be as low as possible. Our web interface can generate property predictions with a single mouse click. And for learning how to code, we wrote our tutorials and documentation for those that have never used python before. 

<!-- REMOVED FOR NOW: Also, be sure attend [our monthly virtual workshop]() if you need help getting started. -->

At the other end of the spectrum, we provide an extremely powerful toolbox and API for experts. Those familiar with the field can view Simmate as an alternative to the [Materials Project](https://materialsproject.org/) stack ([Atomate](https://github.com/hackingmaterials/atomate), [PyMatGen](https://github.com/materialsproject/pymatgen), [MatMiner](https://github.com/hackingmaterials/matminer), and [more](https://matsci.org/)), where we operate under a very different coding philosphy. **Here, usability and readability are our top priorities.** We therefore distribute Simmate as an "all-in-one" package rather than many separate programs. This includes a core material science toolkit, workflow management, database orm, and a website interface. **Simmate also focuses heavily on cloud-based storage**, which enables large scale collaborations and avoids researchers repeating calculations. To learn more about the different design choices made in Simmate compared to competing codes, read through our [comparisons and benchmarks page](https://github.com/jacksund/simmate/tree/main/benchmarks).


## Installation

**Don't panic** if you're new to coding and Python. When you're ready, head to our [tutorials](https://github.com/jacksund/simmate/tree/main/tutorials) where we teach you everything from the beginning.

If you're comfortable with Python, you can install Simmate with...
``` bash
conda install -c conda-forge simmate
```

> :bulb: Simmate itself is <2MB, but when installed to a clean conda environment, the entire download for Simmate and all it's dependencies comes to ~1.2GB. Additional disk space is also needed for optional downloads -- such as [third-party data](https://jacksund.github.io/simmate/simmate/database/third_parties.html).

## Running a Server

Once installed, running a local test server is as simple as...

``` bash
# On first-time setup, you must intialize an empty database.
simmate database reset

# then start the server!
simmate run-server
```

After a few seconds, you can open http://127.0.0.1:8000/ in your browser to view your local server!

> :bulb: Read our [website documentation](https://jacksund.github.io/simmate/simmate/website.html) and [tutorials](https://github.com/jacksund/simmate/tree/main/tutorials) in order to switch to a production-ready server that's accessible through the internet and can be shared among a team.


## A Sneak-Peak of Features

Again, take a look at [our main website](https://simmate.org/) if you'd like to see the end-result of what Simmate has to offer. There are many more functions and utilities once you download Simmate, so this section showcases a few of those features.


1. _**Prebuilt Workflows and Easy Orchestration.**_ All of the most common material properties have workflows ready to go. These range from simple XRD pattern predictions to intensive dynamic simulations. Simmate also builds off of [Prefect](https://github.com/PrefectHQ/prefect) for orchestrating and managing workflows. This means that it's up to you whether to run jobs via (i) an advanced user-interface, (ii) the command-line, or (iii) in custom python scripts:

``` bash
# The command line let's you quickly run a workflow
# from a structure file (CIF or POSCAR).
simmate workflows run relaxation.vasp.matproj --structure NaCl.cif
```

``` yaml
# Workflows can also be ran from YAML-based configuration
# files, such as the one shown here (named `example.yaml`).
# This would be submitted with the command:
#   `simmate workflows run-yaml example.yaml`
workflow_name: relaxation.vasp.matproj
structure: NaCl.cif
command: mpirun -n 8 vasp_std > vasp.out
```

``` python
# Python let's you run workflows within scripts and
# it also enables advanced setting configurations.

from simmate.workflows.relaxation import Relaxation__Vasp__Matproj as workflow

state = workflow.run(structure="NaCl.cif")
result = workflow.result()
```


2. _**A Full-Feature Database.**_ Using all the data on our official site along with your own private data, you can take advantage of Simmate's extremely powerful database that is built off of [Django ORM](https://github.com/django/django). Simmate also brings together third-party databases and their data -- including those like the COD, Materials Project, JARVIS, and others. With so much data, being able to easily download and navigate it is critical:

```python
# Be sure to follow the database tutorial where we build our 
# initial database with the command `simmate database reset`
# and load data with `ExampleTable.load_remote_archive()`
# before running any of the code below.

from simmate.database import connect
from simmate.database.third_parties import MatprojStructure

# EXAMPLE 1: all structures that have less than 6 sites in their unitcell
structures = MatprojStructure.objects.filter(nsites__lt=6).all()

# EXAMPLE 2: complex filtering
structures = MatprojStructure.objects.filter(
    nsites__gte=3,  # greater or equal to 3 sites
    energy__isnull=False,  # the structure DOES have an energy
    density__range=(1,5),  # density is between 1 and 5
    elements__icontains='"C"',  # the structure includes the element Carbon
    spacegroup__number=167,  # the spacegroup number is 167
).all()

# Quickly convert to a pandas dataframe or toolkit structures.
# (note: the toolkit is built off of pymatgen, so it uses the same methods)
df = structures.to_dataframe()
structures = structures.to_toolkit()
```


3. _**Common Task Utilities and Toolbox.**_ A lot of times in research, a new method is needed to analyze a structure, so a prebuilt workflow won't exist for you yet. Here, you'll need common functions ready to go (such as grabbing the volume of a crystal or running symmetry analysis). Our toolkit functions and classes largely inherit from [PyMatGen](https://github.com/materialsproject/pymatgen), which gives you a wide variety of functions to use:

<!-- REMOVED FOR NOW: Our core functions and classes are largely inspired from the [PyMatGen](https://github.com/materialsproject/pymatgen) and [ASE](https://gitlab.com/ase/ase) codes, where we decided to write our own version for speed, readability, and usability: :warning: Our core toolkit is still dependent on pymatgen at the moment. Our reliance on pymatgen will fade over time, but it is important to acknowledge how their software has helped in getting our project off the ground. So thank you to the pymatgen community! -->


``` python
# Load the structure file you'd like to use
from simmate.toolkit import Structure
structure = Structure.from_file("NaCl.cif")

# Access a wide variety of properties. Here are some simple ones.
structure.density
structure.composition.reduced_formula
structure.lattice.volume

# Also access methods that run deformations or analysis on your structure.
structure.make_supercell([2,2,3])
structure.get_primitive_structure()
structure.add_oxidation_state_by_guess()
```


4. _**Ease of Scalability.**_ At the beginning of a project, you may want to write and run code on a single computer and single core. But as you run into some intense calculations, you may want to use all of your CPU and GPU to run calculations. At the extreme, some projects require thousands of computers across numerous locations, including university clusters (using SLURM or PBS) and cloud computing (using Kubernetes and Docker). Simmate can meet all of these needs thanks to integration with [Dask](https://github.com/dask/dask) and [Prefect](https://github.com/PrefectHQ/prefect):
```python
# To run the tasks of a single workflow in parallel, use Dask.
from prefect.task_runners import DaskTaskRunner
workflow.task_runner = DaskTaskRunner()
state = workflow.run(...)

# To run many workflows in parallel, use Prefect.
# Once you configure Prefect, you simply switch
# from using "run" to "run_cloud"
prefect_flow_run_id = workflow.run_cloud(...)

# You can use different combinations of these two parallelization strategies as well!
# Using Prefect and Dask, we can scale out accross various computer resources 
# with a few lines of code.
```


## Need help?

Post your question [here in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 

Even if it's something like "_How do I download all structures with x, y, and z properties?_", let us help out and point you in the right direction!


## Extra resources

- [Getting-started guides and tutorials](https://github.com/jacksund/simmate/tree/main/tutorials)
- [API documentation](https://jacksund.github.io/simmate/simmate.html)
- [Joining our community & helping contribute](https://github.com/jacksund/simmate/tree/main/tutorials/Guides_for_contributors)
- [Requesting a new feature](https://github.com/jacksund/simmate/discussions/categories/ideas)
- [Exploring alternatives to Simmate](https://github.com/jacksund/simmate/tree/main/benchmarks)
- [Citing Simmate](https://doi.org/10.21105/joss.04364)
