
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
