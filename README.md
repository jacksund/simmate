<!-- This displays the Simmate Logo -->
<p align="center" href=https://simmate.org>
   <img src="https://github.com/jacksund/simmate/blob/main/logo/simmate.svg?raw=true" width="700" style="max-width: 700px;">
</p>

<!-- This displays the dynamic badges -->
<p align="center">
<!-- Conda-forge OS support -->
<a href=https://anaconda.org/conda-forge/pymatgen>
    <img src="https://img.shields.io/conda/pn/conda-forge/pymatgen">
</a>
<!-- Github Checks -->
<a href=https://pypi.python.org/pypi/pymatgen/>
    <img src="https://img.shields.io/github/checks-status/materialsproject/pymatgen/master">
</a>
<!-- Github Code Coverage -->
<a href=https://pypi.python.org/pypi/pymatgen/>
    <img src="https://img.shields.io/coveralls/github/materialsproject/pymatgen">
</a>
</p>

<!-- 
I use html format above to center the objects. Otherwise I could simple markdown like this:
![Simmate Logo](https://github.com/jacksund/simmate/blob/main/logo/simmate.svg?raw=true)
Read here for info on markdown, badges, and more:
[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
[Shields Badges](https://shields.io/)
-->

## Welcome!

If you are brand-new to Simmate, jump over to our main website [simmate.org](simmate.org) and take a look at what we have to offer. This page is for when you're ready to use Simmate in your own research and access some advanced functionality. Our software is open-source and free to use, so come back to try it when you're ready! 


## What is Simmate?

The Simulated Materials Ecosystem (Simmate) is a toolbox and helper for computational materials research. It lets you explore various crystal databases, predict new materials, and quickly calculate properties (electronic, elastic, thermodynamic, and more).

Computational research can be intimidating because there are so many programs to choose from, and it's hard to mix-and-match them for your specific project. Simmate aims to be the glue between all these different programs, databases, and utilities. We do the heavy lifting, and explain these other programs to you along the way. 

Even if you consider yourself an experimentalist and have little-to-no coding experience, Simmate's barrier to entry is built to be as low as possible -- with a heavy emphasis on clear and beginner-oriented tutorials and documentation. Simmate is designed to guide your studies and generate property predictions with a single mouse click.

At the other end of the spectrum, we provide an extremely powerful toolbox and API for experts. Those familiar with the field can view Simmate as an alternative to the [Materials Project](https://materialsproject.org/) stack ([Atomate](https://github.com/hackingmaterials/atomate), [PyMatGen](https://github.com/materialsproject/pymatgen), [MatMiner](https://github.com/hackingmaterials/matminer), and [more](https://matsci.org/)), where we opperate under a very different coding philosphy. **Here, usability and readability are our top priortities.** The first step toward that end is an "all-in-one" package rather than many separate programs. This includes a core material science framework, workflow management, database orm, and a website interface. To learn more about the different design choices made in Simmate compared to competing codes, read through our [COMPARISONS_and_BENCHMARKS page]() and our [initial publication]().

## Installation

**Don't panic** if your new to coding and Python. When you're ready to start learning, advance to our [15min Start-Up Tutorial]() where we teach you everything from the beginning.

If you're confortable with Python, you can install Simmate with...
```
conda install -c conda-forge simmate
```


## A Sneak-Peak of Features (for experts)

Again, take a look at [our main website](simmate.org) if you'd like to see the end-result of what Simmate has to offer. This section showcases some features of downloading and using Simmate yourself.

1. _**Prebuilt Workflows and Easy Orchestration.**_ All of the most common material properties have workflows ready to go. These range from simple XRD pattern predictions to intensive elastic calculations. Simmate also builds off of [Prefect](https://github.com/PrefectHQ/prefect) for orchestrating and managing workflows. So it's up to you whether to run jobs via an advanced user-interface (shown below) or in custom scripts:

<!-- This is an image of the Prefect UI -->
<p align="center" style="margin-bottom:40px;">
<img src="https://raw.githubusercontent.com/PrefectHQ/prefect/master/docs/.vuepress/public/orchestration/ui/dashboard-overview2.png"  height=440 style="max-height: 440px;">
</p>

```python
# Load the structure file you'd like to use
from simmate import Structure
my_structure = Structure.from_file('NaCl.cif')

# Load the workflow you'd like and run it!
from simmate.workflows import RelaxStructure
result = RelaxStructure.run(structure=my_structure)
```

2. _**A Full-Feature Database.**_ Using all the data on our official site along with your own private data, you can take advantage of Simmate's extremely powerful database API that is built off of [Django ORM](https://github.com/django/django). Simmate also brings together third-party databases and their data -- including those like ICSD, OCD, Materials Project, AFLOW, JARVIS, and others. With so much data, being able to easily download and navigate it is critial:

```python
# Here are some examples of querying the Simmate database for specific structures
from simmate import Structure_Database

# EXAMPLE 1: all structures that have less than 6 sites in their unitcell
structures = Structure_Database.objects.filter(nsites__lt=6)

# EXAMPLE 2: all MoS2 structures that are less than 10g/A^3 and have a bulk
# modulus greater than 0.5
structures = Structure_Database.objects.filter(
   formula="MoS2",
   density__lt=10,
   elastic__bulk_modulus__gt=0.5,
)
```

3. _**Ease of Scalability.**_ At the beginning of a project, you may want to write and run code on a single computer and single core. But as you run into some intense calculations, you may want to use all of your CPU and GPU to run calculations. At the extreme, some projects require thousands of computers across numerous locations, including university clusters (using SLURM or PBS) and cloud computing (using Kubernetes and Docker). Simmate can meet all of these needs with ease:

```python
# To run the tasks of a single workflow in parallel, use Dask!
from prefect.executors import DaskExecutor
workflow.executor = DaskExecutor()
result = workflow.run()

# To run many workflows in parallel, use Prefect!
from prefect import Client
client = Client()
client.create_flow_run(
   project_name="Example-Project",
   flow_name="Example-Workflow",
   parameters={"timelimit": 50},
)

# You can use different combinations of these two parallelization strategies as well!
# Using Prefect and Dask, we can scale out accross various computer resources 
# with a few lines of code.
```

4. _**Common Task Utilities and Toolbox.**_ A lot of times in research, a new method is needed to analyze a structure, so a prebuilt workflow won't exist for you yet. Here, you'll need common functions ready to go (such as grabbing the volume of a crystal or running symmetry analysis). Our core functions and classes are largely inspired from the [PyMatGen](https://github.com/materialsproject/pymatgen) and [ASE](https://gitlab.com/ase/ase) codes, where we decided to write our own version for speed, readability, and usability:
```python
# Load the structure file you'd like to use
from simmate import Structure
structure = Structure.from_file('NaCl.cif')

# Access a wide variety of properties. Here are some simple ones.
structure.density
structure.composition.reduced_formula
structure.lattice.volume

# Also access methods that run deformations or analysis on your structure.
structure.get_supercell([2,2,2])
structure.get_conventional_unitcell()
structure.get_oxidation_states()
```

## Need help?

Post your question [here in our discussion section](). 

Even if it's something like "_How do I download all structures with x, y, and z properties?_", let us help out and point you in the right direction!

## Extra resources

- [Getting-started guides and tutorials]()
- [Joining our community & helping contribute]()
- [Requesting a new feature]()
- [Exploring alternatives to Simmate]()
