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
<!-- PyPI downloads per month -->
<a href=https://pypi.python.org/pypi/pymatgen/>
    <img src="https://img.shields.io/pypi/dm/pymatgen">
</a>
<!-- Conda-forge download total -->
<a href=https://anaconda.org/conda-forge/pymatgen>
    <img src="https://img.shields.io/conda/dn/conda-forge/pymatgen">
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
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI download total](https://img.shields.io/pypi/dm/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![Conda-forge download total](https://img.shields.io/conda/dn/conda-forge/pymatgen)](https://anaconda.org/conda-forge/pymatgen)
[![Conda-forge OS support](https://img.shields.io/conda/pn/conda-forge/pymatgen)](https://anaconda.org/conda-forge/pymatgen)
[![Github Repo Size](https://img.shields.io/github/repo-size/materialsproject/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![PyPI Python Version Support](https://img.shields.io/pypi/pyversions/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![Total Line Count](https://img.shields.io/tokei/lines/github/pandas-dev/pandas)](https://pypi.python.org/pypi/pymatgen/)
[![Github Checks](https://img.shields.io/github/checks-status/materialsproject/pymatgen/master)](https://pypi.python.org/pypi/pymatgen/)
[![Github Code Coverage](https://img.shields.io/coveralls/github/materialsproject/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
Read here for info on markdown, badges, and more:
[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
[Shields Badges](https://shields.io/)
-->

## Welcome!

If you are brand-new to Simmate, you should jump over to our main website [simmate.org](simmate.org) and take a look at what we have to offer. This page is for when you're ready to bring your lab to the next level and start using Simmate in your own research. Simmate is open-source and free to use, so come back to try it yourself when you're ready! 


## What is Simmate?

The Simulated Materials Ecosystem (Simmate) is the ultimate toolbox and helper for computational materials research. 

Even if you consider yourself an experimentalist, Simmate's barrier to entry is built to be as low as possible. In fact, you don't need to know how to code at all. Simmate is designed to guide your studies and generate property predictions with a single mouse click. Computational research can be intimidating because there are so many programs to choose from, and it's hard to mix-and-match them for your specific project. Simmate aims to be the glue between all these different programs, databases, and utilities. We do the heavy lifting, and explain these other programs to you along the way.

At the other end of the spectrum, we provide an extremely powerful API for experts. Those familiar with the field can view Simmate as an alternative to the [Materials Project](https://materialsproject.org/) stack ([Atomate](https://github.com/hackingmaterials/atomate), [PyMatGen](https://github.com/materialsproject/pymatgen), [MatMiner](https://github.com/hackingmaterials/matminer), and [more](https://matsci.org/)), where we opperate under a very different coding philosphy. **Here, usability and readability are our top priortities.** The first step toward that end is an "all-in-one" package rather than many separate programs. This includes a core material science framework, workflow management, database orm, and a website interface. To learn more about the different design choices made in Simmate compared to competing codes, [see here]()

## Installation

**Don't panic** if your new to coding coding and Python. When you're ready to start learning, you can advance to our [15min Start-Up Tutorial]() where we teach you everything from the beginning.

If you're confortable with Python, you can install Simmate with...
```
conda install -c conda-forge simmate
```

## A Sneak-Peak of Features

Again, take a look at [our main website](simmate.org) if you'd like to see the end-result of what Simmate has to offer. This secton showcases some features of downloading and using Simmate yourself.

1. _**Prebuilt Workflows and Easy Orchestration.**_ All of the most common material properties have workflows ready to go. These range from simple XRD pattern predictions to intensive dielectric calculations. Simmate also builds off of [Prefect](https://github.com/PrefectHQ/prefect) for orchestrating and managing workflows. So it's up to you whether to run jobs via an advanced user-interface (shown below) or in custom scripts:

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

2. _**A Full-Feature Database.**_ Using all the data on our official site or your personal data, you can take advantage of Simmate's extremely powerful database API that is built off of [Django ORM](https://github.com/django/django). Simmate also brings together other databases and their data -- including those like ICSD, OCD, Materials Project, AFLOW, JARVIS, and others. With so much data, being able to navigate it is critial:

```python
# Here are some examples of querying the Simmate database for specific structures
from simmate.database import Structure

# EXAMPLE 1: all structures that have less than 6 sites in their unitcell
structures = Structure.objects.filter(nsites__lt=6)

# Example 2: all MoS2 structures that are less than 10g/A^3 and have a bulk modulus greater than 0.5
structures = Structure.objects.filter(
   formula="MoS2",
   density__lt=10,
   elastic__bulk_modulus__gt=0.5,
)
```

3. _**Ease of Scalability.**_ At the beginning of a project, the user may want to write and run their code on a single computer and single core. But as you run into some intense calculations, you may want to use all of your CPU and GPU to run calculations. At the extreme, some projects require thousands of computers across numerous locations, including university clusters (using SLURM or PBS) and cloud computing. Simmate can meet all of these needs with ease:

```python
# To run the tasks of a single workflow in parallel, use Dask!
from prefect.executors import DaskExecutor
workflow.executor = DaskExecutor()
result = workflow.run()

# To run many workflows in parallel, use Prefect!
from prefect import Client
client = Client()
client.create_flow_run(project_name="Example-Project", flow_name="Example-Workflow", parameters=...) 

# You can using different combinations of these two parallelization strategies as well!
# Using Prefect and Dask, we can scale out accross various computer resources with a few lines of code.
```

4. _**Common Task Utilities and Toolbox.**_ A lot of times in research, you're coming up with a new method to analyze some structure, so a prebuilt workflow won't exist for you yet. Here, you need common functions ready to go (such as grabbing the volume of a crystal or running symmetry analysis). Our core functions and classes are largely inspired from the [PyMatGen](https://github.com/materialsproject/pymatgen) and [ASE](https://gitlab.com/ase/ase) codes, where decided to write our own version for speed, readability, and usability:
```python
# Load the structure file you'd like to use
from simmate import Structure
structure = Structure.from_file('NaCl.cif')

# Access a wide variety of properties and method. Here are some simple ones.
structure.density
structure.composition.reduced_formula
structure.lattice.volume
```

## Need help?

Post your question [here in our discussion section](). 

Even if it's as simple as "_How do I download all structures with x, y, and z properties?_", let us help out and point you in the right direction!

## Extra resources

contributing, tutorials, docs, etc.


<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



Should I put this code in the contributing docs?
## Coding Philosphy

“If I have seen further it is by standing on the shoulders of Giants” -Isaac Newton (1675)
Though there's [more behind this quote](https://en.wikipedia.org/wiki/Standing_on_the_shoulders_of_giants) that I might want to used instead.

There are many different design choices made in Simmate compared to competing codes such as in the Materials Project, JARVIS, AFLOW, and others. When reading through our documentation and code, some of our core beliefs should stand out immediately:

1. **Code is more often read than written.** For this reason, we believe code readability is extremely important. You'll find that we have an extremely large number of comments in our code -- there's actually more comments than code in many cases. This makes reading and understand functions much clearer. Users shouldn't treat their functions as a black-box, but instead as something they can read through to understand better - even if they aren't a python expert.
2. **Opinionated code enhances usability.**

**Immediate local exectution**. Other codes require complex setups such as a database server and worker processes, whereas these are completely optional in Simmate. If you'd like to test out running a workflow immediately and directly in your test enviornment, you can! For example, how do I relax my crystal structure using DFT? All you need is your crystal structure and the following code:

Simmate includes all of the components you'll need including a core material science framework, workflow management, database orm, and a website interface. We adopt opinionated, high-level, and batteries-included coding philosophies, and we love building off of highly respected packages that do the same. The core "giants" that we build off of are [Django](https://github.com/django/django) and [Prefect](https://github.com/PrefectHQ/prefect), while lower level methods are sped up or parallelized by [Numpy](https://github.com/numpy/numpy), [Numba](https://github.com/numba/numba), and [Dask](https://github.com/dask/dask). The functionality of all these codes are built-in and you can use as much or as little of them as you'd like. We've also accounted for the complex scaling of your computer resources using modern Executor/Queue models -- whether you're working on a single computer for testing or want to submit thousands of VASP jobs to multiple HPC clusters (using a mix of SLURM or PBS queue systems), you can do that and do it quickly. Take a look at [our original publication](google.com) and [our benchmarks against other codes](google.com) to see more.

Table of external codes that we support like vasp, pymatgen, django... (see table below)



Component | Package | Other Packages (not used)
------------ | ------------- | -------------
Materials Science | PyMatGen | ASE
Website Backend Framework | Django | Flask
Website Frontend Framework | None | Angular, React, Vue.js
Website CSS | Bootstrap | ...
Templating | Django-templates | Jinja
Database ORM | Django-ORM | SQLAlchemy
Database API | None | RESTfulAPI (django-REST), GraphQL (Graphene)
Database backend | SQLite | PostgreSQL, MongoDB
Dataframe storage | CSV | JSON, YAML
Dataframe utilities | Pandas | ...
Workflow Engine | Prefect | FireWorks, Luigi, AirFlow
Workflow Management | Prefect-cloud | Prefect-server, FireWorks
Workflow Execution | None (local) | Dask, FireWorks
Workflow Library | None | Atomate
JIT Task Management | None | Prefect, Custodian
Desktop App | None | Kivy, Django (test server), PyQt
Continuous Integration | GithubActions | TravisCI, CircleCI
Plotting | None | MatPlotLib, Plotly, Bokeh, Seaborn
3D Modeling | Blender (bpy) | VTK
3D App | Verge3D | Three.js
Testing | PyTest | UnitTest
Density Function Theory | VASP | ABINIT, CASTEP
Datamining Engine | SciKit-Learn | TensorFlow, Keras
Datamining Library | None | Matminer
Reference Style | None | BibTex, RIS
Reference Management | SciWheel | Mendeley, Zotero, EndNote
SVG Editting | Inkscape | Adobe Illustrator
Graphics Editting | GIMP | Adobe Photoshop
Command Line Interface | Click | Argparse, Python-Fire
Code Formatting | Black | PyLint

This belongs elsewhere maybe?
4. **Clear, Up-Front Settings**. Many material science codes that map to DFT codes (like VASP, ABINIT, and others) often obscure what DFT setting they are using from the user. Even computational experts can have a difficult time figuring out which settings are being used and how dynamic ones are being set. In Simmate, a single DFT task and it's settings are made to be clear and obvious:
```python
# import the base Task for your desired calculator. Here we use VASP
from simmate.calculators.vasp.tasks.base import VaspTask

# Configure the VASP calculation to your liking
# NOTE: we can make settings dynamic to each structure using tags like "_per_atom" like shown below
class ExampleVaspCalculation(VaspTask):

    # The default settings to use for this static energy calculation.
    incar = dict(
        EDIFF_per_atom=1.0e-07,
        ENCUT=520,
        NSW=0,
        KSPACING=0.5,
    )

    # We will use the PBE functional with all the default POTCARs
    functional = "PBE"

# if you'd like to run this task individually (without putting it in a workflow)
result = task.run(structure=my_structure)

# or you build it into a workflow and then run it
with Flow("a-single-vasp-calc") as my_workflow:
   structure = Parameter("structure")
   result = ExampleVaspCalculation(structure)
result = my_workflow.run()
```
