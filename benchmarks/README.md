
# Comparisons and Benchmarks

This page gives an overview of alternatives to Simmate and also benchmarks some of our core features. Because there are so many subcomponents, we therefore organize our comparisons by use-case below:

1. [Overview](#overview)
2. [Toolkit](#toolkit)
3. [Database](#database)
4. [Workflow Engine](#workflow-engine)
5. [Workflow Library](#workflow-library)
6. [Apps](#apps)

There are always new programs being developed and new features being added to Simmate, so our comparisons and benchmarks may not be up to date. If you would like us to mention a software or benchmark a new feature, let us know!

</br>

## Overview

Simmate aims to be a full framework AND toolset, which means our overall package is largely the combination of many smaller modules and features. Meanwhile, most other teams/softwares have their framework and toolsets broken into smaller, independent packages. 

To illustrate this difference, a perfect example is the collection of softwares for the Materials Project. Their organization is powered by many smaller packages, each with a specific use-case. You can view all of these on [their github organization page](https://github.com/materialsproject). Many of their packages have direct analogs to the parts of Simmate:

Component | Materials Project | Simmate
------------ | ------------- | -------------
Defining and submitting workflows | [fireworks](https://github.com/materialsproject/fireworks) | [prefect](https://github.com/PrefectHQ/prefect)
MatSci workflow library | [atomate](https://github.com/hackingmaterials/atomate) | our `workflows` module
Tasks & Error handling | [custodian](https://github.com/materialsproject/custodian) | our `engine` module
IO to different programs | [pymatgen.io](https://github.com/materialsproject/pymatgen) | our `apps` module
Database backend | [MongoDB](https://github.com/mongodb/mongo-python-driver) | any engine supported by [django](https://github.com/django/django)
Database API | [emmet](https://github.com/materialsproject/emmet) | our `database.base_data_types` module 
Web API | [mapidoc](https://github.com/materialsproject/mapidoc) | built dynamically by our `website` module
Utilities & toolkit | [pymatgen](https://github.com/materialsproject/pymatgen) | our `toolkit` module (built w. `pymatgen`)
Website components | [crystaltoolkit](https://github.com/materialsproject/crystaltoolkit) | our `website.core_components` module
Third-party Data | [mpcontribs](https://github.com/materialsproject/MPContribs) | our `database.third_parties` module 
*more comparisons can be made too!* | ..... | ....

There are more comparisons that can be made between this organization and Simmate, but this table gets to the major analogies between the two.

In addition to the Materials Project, there are many other organizations (the AFLOW and AiiDA ecosystems) that have analogous components to those in Simmate. A detailed comparison to each of these is beyond the scope of this page, but overall, we can say that the biggest differences are...

1. Simmate is an all-in-one package while others break-up their components
    - This is much more beginner-friendly and helps non-coders understand advanced features without jumping between several github repos and api pages.
    - When building new packages off of Simmate, we favor building features as custom apps that easily be incorporated to our source-code (as individual apps). This is very different from (and easier than) building a new package entirely -- like you'd do with other ecosystems.

2. Simmate prefers the use of large-scale popular packages over custom implementations
    - Whereas other ecosystems write workflow managers and task distribution from scratch, we uses popular packages like Prefect, Dask, and Django. This greatly facilitates the addition of new features while also enabling best-practices with the communities outside of materials science.
    - The exception to this rule is with materials science software. There are several cases where we create a new implementation from scratch -- as we are materials chemists and can't help trying to improve upon these codes! An example of this includes our effort to make a new module for evolutionary structure prediction.

3. Simmate is younger and smaller than other ecosystems
    - The python ecosystem has grown substanially over time, and we can easily take advantage of new softwares and packages, whereas other ecosystems are often tied to outdated practices or packages.
    - Other ecosystems have built up massive libraries and toolkits, where we are catching up on the diverse set of functionality (though we are catching up quickly!).
    - Because we still have a small user-base, our team will be able to prioritize your work if you post a question or need hands-on helps.
    - Our test suite is not as encompassing as other ecosystems, but we are slowly building up functionality over time.


</br></br>

## Toolkit

The `simmate.toolkit` module is currently an extension of `pymatgen`. It some cases it can be also be viewed fork of `pymatgen`, but our added features/reorganization is limited for now.

### `toolkit` alternatives
- [pymatgen](https://github.com/materialsproject/pymatgen)
- [ase](https://gitlab.com/ase/ase)
- [jarvis-tools]()
    
### `toolkit.base_data_types` alternatives
- [pymatgen.core](https://github.com/materialsproject/pymatgen)
- [ase](https://gitlab.com/ase/ase)

### `toolkit.featurizers` alternatives
- [matminer](https://github.com/hackingmaterials/matminer)

### `toolkit.structure_creation` alternatives
- [pyxtal](https://github.com/qzhu2017/PyXtal)
- [pymatgen.analysis.structure_prediction](https://pymatgen.org/pymatgen.analysis.structure_prediction.html)

### `toolkit.structure_prediction.evolution` alternatives
- [uspex](https://uspex-team.org/)
- [xtalopt](http://xtalopt.github.io/)
- [calypso](http://www.calypso.cn/)
- [ase.ga](https://wiki.fysik.dtu.dk/ase/ase/ga/ga.html)
- [airss](https://airss-docs.github.io/)
- [gasp](https://github.com/henniggroup/GASP-python)

### `toolkit.diffusion` alternatives
- [pymatgen.analysis.diffusion](https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion)

</br>

## Database

The `simmate.database` module is an independent implementation that builds off of Django ORM and the schemas are largely inspired by [emmet](https://github.com/materialsproject/emmet) and [qmpy](https://static.oqmd.org/static/docs/index.html).

### `database.base_data_types` alternatives
- [emmet](https://github.com/materialsproject/emmet)
- [qmpy](https://static.oqmd.org/static/docs/index.html)

### `database.third_parties` alternatives
- [mpcontribs](https://github.com/materialsproject/MPContribs)
- [matminer.data_retrieval](https://matminer.readthedocs.io/en/latest/matminer.data_retrieval.html)
- [pymatgen.ext](https://pymatgen.org/pymatgen.ext.html)
- [OPTIMADE APIs](http://www.optimade.org/)

### `database.workflow_results` alternatives
- [atomate](https://github.com/hackingmaterials/atomate)
- [qmpy](https://static.oqmd.org/static/docs/index.html)
- [matador](https://github.com/ml-evs/matador)

</br>

## Workflow Engine

The `simmate.engine` module builds off of Prefect where a lot of the core functionality is inspired by [fireworks](https://github.com/materialsproject/fireworks) and [custodian](https://github.com/materialsproject/custodian).

### `engine.s3task` alternatives
- [custodian](https://github.com/materialsproject/custodian)

### `engine.workflow` alternatives
- [fireworks](https://github.com/materialsproject/fireworks)
- [aiida-core](https://github.com/aiidateam/aiida-core)

</br>

## Workflow Library

The `simmate.workflows` module is an independent implementation of materials science workflows where much of our inspiration comes from [atomate](https://github.com/hackingmaterials/atomate).

### `workflows` alternatives
- [atomate](https://github.com/hackingmaterials/atomate)
- [aiida-common-workflows](https://github.com/aiidateam/aiida-common-workflows)
- [abipy](https://github.com/abinit/abipy)

</br>

## Apps

The `simmate.apps` module is an independent implementation of materials science workflows where much of our inspiration comes from [pymatgen.io](https://github.com/hackingmaterials/atomate) and [ase.calculators](). In several cases, we use some of pymatgen/ase functions directly in our module -- serving as a placeholder until we refactor/fork the their implementation.

### `apps` alternatives
- [pymatgen.io](https://pymatgen.org/pymatgen.io.html)
- [ase.calculators](https://github.com/rosswhitfield/ase/tree/master/ase/calculators)



# Overview of Softwares and Utilities used by our lab

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
Command Line Interface | Click | Argparse, Python-Fire, Typer
Code Formatting | Black | PyLint
