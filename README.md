# Simmate (SME - Simulated Materials Ecosystem)

The dynamic badges are linked to pymatgen right now because I'm just testing out which ones I'd like to try.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI download total](https://img.shields.io/pypi/dm/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![Conda-forge download total](https://img.shields.io/conda/dn/conda-forge/pymatgen)](https://anaconda.org/conda-forge/pymatgen)
[![Conda-forge OS support](https://img.shields.io/conda/pn/conda-forge/pymatgen)](https://anaconda.org/conda-forge/pymatgen)
[![Github Repo Size](https://img.shields.io/github/repo-size/materialsproject/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![PyPI Python Version Support](https://img.shields.io/pypi/pyversions/pymatgen)](https://pypi.python.org/pypi/pymatgen/)
[![Total Line Count](https://img.shields.io/tokei/lines/github/pandas-dev/pandas)](https://pypi.python.org/pypi/pymatgen/)
[![Github Checks](https://img.shields.io/github/checks-status/materialsproject/pymatgen/master)](https://pypi.python.org/pypi/pymatgen/)
[![Github Code Coverage](https://img.shields.io/coveralls/github/materialsproject/pymatgen)](https://pypi.python.org/pypi/pymatgen/)

This readme is not complete yet. Read here for more info on markdown, badges, and more:
[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
[Shields Badges](https://shields.io/)

## Welcome!

There are tons of programs available in computational materials science, and it can become overwhelming to pick which to use and how to mix-and-match them for your specific project. 

That's why we've made Simmate! We aim to be the glue between all these different programs, databases, and utilities.

Simmate has everything you need for materials chemistry research all in one repo. Whether you're an experimental or computational scientist, this program is built to scale for your needs. Jumpstart your research from here and hit the ground running.

## Simmate is built for everyone

**For Readers:** Not ready to download and try things yourself? No worries! Just take a look at our website [simmate.org](simmate.org) that shows all of the calculations that we've done already. Explore what we have to offer, and then come back to try it yourself when you're ready!

**For Beginners:** We were all first-year graduate students before too, so our guides are written with that in mind. Take your research question and look for a workflow we've prebuilt that does it for you. For example, how do I relax my crystal structure using DFT? All you need is your crystal structure and the following code:
```python
# Load the structure file you'd like to use
from simmate import Structure
my_structure = Structure.from_file('NaCl.cif')

# Load the workflow you'd like to use
from simmate.workflows import RelaxStructure

# Now run the workflow!
result = RelaxStructure.run(structure=my_structure)
```
If you're new to coding and Python, you should go through our walkthrough tutorial located here: [30min Start-Up Tutorial](google.com)

**For Experts:** Simmate includes all of the components you'll need including a core material science framework, workflow management, database orm, and a website interface. We adopt opinionated, high-level, and batteries-included coding philosophies, and we love building off of highly respected packages that do the same. The core "giants" that we build off of are [Django](https://github.com/django/django) and [Prefect](https://github.com/PrefectHQ/prefect), while lower level methods are sped up or parallelized by [Numpy](https://github.com/numpy/numpy), [Numba](https://github.com/numba/numba), and [Dask](https://github.com/dask/dask). The functionality of all these codes are built-in and you can use as much or as little of them as you'd like. We've also accounted for the complex scaling of your computer resources using modern Executor/Queue models -- whether you're working on a single computer for testing or want to submit thousands of VASP jobs to multiple HPC clusters (using a mix of SLURM or PBS queue systems), you can do that and do it quickly. Take a look at [our original publication](google.com) and [our benchmarks against other codes](google.com) to see more.

## Where does Simmate fall short?

While we give you the most common materials science analysis, there are always places where other codes offer more advanced customization for expert users. Simmate will teach you the basics and then tell you where to go from there. For example, we love pointing users to the codes that inspired us, where some of the big ones are [PyMatGen](https://github.com/materialsproject/pymatgen), [ASE](https://gitlab.com/ase/ase), [MatMiner](https://github.com/hackingmaterials/matminer), [Custodian](https://github.com/materialsproject/custodian), and [Fireworks](https://github.com/materialsproject/fireworks).






Fractured Hierarchical Architecture for High-Throughput Diffusion Analysis

“If I have seen further it is by standing on the shoulders of Giants” -Isaac Newton (1675)
Though there's [more behind this quote](https://en.wikipedia.org/wiki/Standing_on_the_shoulders_of_giants) that I might want to used instead.


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
