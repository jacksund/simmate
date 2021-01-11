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

Simmate is the Simulated Materials Ecosystem which has everything you need for materials chemistry research all in one repo. This includes a core material science framework, workflow management, database orm, and a website interface. 

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
