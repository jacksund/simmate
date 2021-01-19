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

_**For Readers:**_ Not ready to download and try things yourself? No worries! Just take a look at our website [simmate.org](simmate.org) that shows all of the calculations that we've done already. Explore what we have to offer, and then come back to try it yourself when you're ready!

_**For Beginners:**_ We were all first-year graduate students before too, so our guides are written with that in mind. Take your research question and look for a workflow we've prebuilt that does it for you. For example, how do I relax my crystal structure using DFT? All you need is your crystal structure and the following code:
```python
# Load the structure file you'd like to use
from simmate import Structure
my_structure = Structure.from_file('NaCl.cif')

# Load the workflow you'd like to use
from simmate.workflows import RelaxStructure

# Now run the workflow!
result = RelaxStructure.run(structure=my_structure)
```

_**For Experts:**_ Simmate includes all of the components you'll need including a core material science framework, workflow management, database orm, and a website interface. We adopt opinionated, high-level, and batteries-included coding philosophies, and we love building off of highly respected packages that do the same. The core "giants" that we build off of are [Django](https://github.com/django/django) and [Prefect](https://github.com/PrefectHQ/prefect), while lower level methods are sped up or parallelized by [Numpy](https://github.com/numpy/numpy), [Numba](https://github.com/numba/numba), and [Dask](https://github.com/dask/dask). The functionality of all these codes are built-in and you can use as much or as little of them as you'd like. We've also accounted for the complex scaling of your computer resources using modern Executor/Queue models -- whether you're working on a single computer for testing or want to submit thousands of VASP jobs to multiple HPC clusters (using a mix of SLURM or PBS queue systems), you can do that and do it quickly. Take a look at [our original publication](google.com) and [our benchmarks against other codes](google.com) to see more.

## Are there similar codes to ours?

While we give you the most common matsci analyses, there are always places where other codes offer more advanced customization for expert users. That's generally the case with high-level packages like ours. Simmate will teach you the basics and then tell you where to go from there. For example, we love pointing users to the codes that inspired us, where some of the big ones are [PyMatGen](https://github.com/materialsproject/pymatgen), [ASE](https://gitlab.com/ase/ase), [MatMiner](https://github.com/hackingmaterials/matminer), [Custodian](https://github.com/materialsproject/custodian), and [Fireworks](https://github.com/materialsproject/fireworks). You can think of Simmate as a combination of all of these, where the original codes have a lot more functionality. We are working hard to catch up, but they've had a decade headstart in most cases and we need to give credit to all of those contributors and their hard work. Simmate wouldn't be possible without their findings. We do believe the changes we've made are for the better and like to show our benchmarks and simple api to prove it.

## Integrations and Core Components

Table of external codes that we support like vasp, pymatgen, django... (see table below)

## Installation

If you're new to coding and Python, you should go through our walkthrough tutorial located here: [30min Start-Up Tutorial](google.com)
Otherwise, you can install simmate quickly and easily with...
```
conda install -c conda-forge simmate
```

## Need help?

Post here in our github using [this link here](google.com)

## Extra resources

contributing, tutorials, docs, etc.


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

# LOGO + GRAPHIC DESIGN NOTES
Name: Simmate (Simulated Materials Ecosystem) 
Overall design: MinimalistBecause it's a software package at its core, I like the minimalist logo designs (here are some examples) and that'd be in line with most python packages. I give some examples of this below.
Color Scheme: up to youMy first thought was a green-based palette to go with "Ecosystem" in the name, but you can mess with whatever.
About the software, website, & company:You can think of Simmate as "a toolbox and library for materials chemistry", where it includes...an online database. You can search any compound you want and then look at its calculated properties. It also brings together other databases and their data -- so a webpage for one material will link to our "competitors" as well. Essentially it serves as a Google for materials and their calculated properties.prebuilt workflows. Say a user has a new material of their own and wants to calculate how conductive it would be, but they don't know how to do those calculations. Our code takes their structure and will run everything for them.common task utilities. A lot of times in research, you're coming up with a new method to analyze some structure, so a prebuilt workflow won't exist for you yet. Here, you need common functions ready to go(such as grabbing the volume of a crystal or running symmetry analysis). That way users can quickly build their own personal workflow without starting from scratch.computing scalability. At the beginning of a project, the user may want to write and run their code on a single computer and single core (this is how 99% of programs work). But as you run into some intense calculations, you may want to use all of your CPU and GPU to run calculations (much like video games do). At the extreme, some projects require thousands of computers across numerous resources, including university HPC clusters and cloud computing. You can easily set up any configuration of resources with only a few lines of code and minimal knowledge of firewalls + internet ports.
Places to draw inspiration from:Don't take this section as me saying "try to incorporate these ideas", but instead as some resources if you want them. I don't want to railroad your thought process and work, so it may even be useful to read this section after you feel stuck and need some more tips. Use as much or as little of this section as you want (or even ignore it).materials chemistry. The most common geometric shapes in my field are the tetrahedral (tetrahedron), octahedral, and cube. Other more complex but less common shapes are here: https://en.wikipedia.org/wiki/Coordination_geometryconnectivity and modularity. Piecing a bunch of things together is a big part of Simmate. The workflows can be thought of a network of calculations; the database as connecting a bunch of materials and other databases; and the code connects super large open-source projects and programs. Therefore, I've been checking out google images for searches like "modular icon" and "network graph icon".competing codes' logos. I give a lot of info here, but really this is just so you can look at competing webpages and see what their logos are like (I'm not a fan of most of them, but think a few are clever). Simmate is really a rewrite of the Materials Project with some key differences and updates in coding philosophy. For example, MP writes many small packages that can be overwhelming, and their many codes are disorganized, slow, and of varying standards as a result too. For all of their logos in one place, check out this link. The key ones are Materials Project (for online database), Atomate (for prebuilt workflows), Fireworks (for computing scalability), and pymatgen (for common task utilities). Meanwhile Simmate is an all-in-one "batteries-included" package that has all of these features ready to go -- you don't have to learn and download a bunch of different programs; only one. Other people that do the same but are much less successful are JARVIS, AFLOW, COD, and ICSD.supporting codes' logos. I don't code everything from scratch, but instead build off of world-leading codes that thousands of people support and are free+open-source. The big two are Django and Prefect. As a side note, both of these sites have some great "modern minimalistic" logo + icon design that I like.

