
# Welcome!

<!-- This displays the Simmate Logo -->
<p align="center" href=https://simmate.org>
   <img src="https://github.com/jacksund/simmate/blob/main/src/simmate/website/static_files/images/simmate-logo-dark.svg?raw=true" width="80%" style="max-width: 1000px;">
</p>

<!-- 
I use html format above to center the objects. Otherwise I could simple markdown like this:
![Simmate Logo](https://github.com/jacksund/simmate/blob/main/logo/simmate.svg?raw=true)
Read here for info on markdown, badges, and more:
[Github-flavored Markdown](https://guides.github.com/features/mastering-markdown/)
[Shields Badges](https://shields.io/)
-->

<!-- This displays the dynamic badges -->
<p align="center">
<!-- Conda-forge OS support -->
<a href="https://anaconda.org/conda-forge/simmate">
    <img src="https://img.shields.io/badge/-Windows | Mac | Linux-00666b">
</a>
<!-- Pricing statement for begineers that are new to github -->
<a href="https://anaconda.org/conda-forge/simmate">
    <img src="https://img.shields.io/badge/-Free & Open Source-00666b">
</a>
<!-- link to JOSS paper -->
<a href="https://doi.org/10.21105/joss.04364">
    <img src="https://img.shields.io/badge/-DOI:10.21105/joss.04364-00666b">
</a>

</br>
<!-- Link to Githbub -->
<a href="https://github.com/jacksund/simmate">
    <img src="https://img.shields.io/badge/-Source Code-/?logo=github&color=00666b&logoColor=white">
</a>
<!-- Link to Website -->
<a href="https://simmate.org/">
    <img src="https://img.shields.io/badge/-Website-/?logo=iCloud&color=00666b&logoColor=white">
</a>
<!-- link to change-log -->
<a href="https://jacksund.github.io/simmate/change_log/">
    <img src="https://img.shields.io/badge/-Changes & Updates-/?logo=git-extensions&color=00666b&logoColor=white">
</a>
</p>

--------------------------------------------------------------------------------

## Before you begin

This website holds all of our tutorials & guides. Before getting started here, you may way to check out... 

- our main website at [simmate.org](https://simmate.org/)
- our source code [github.com/jacksund/simmate](https://github.com/jacksund/simmate)

--------------------------------------------------------------------------------

## What is Simmate?

The Simulated Materials Ecosystem (Simmate) is a toolbox and framework for computational materials research. It lets you explore various crystal databases, predict new materials, and quickly calculate properties (electronic, elastic, thermodynamic, and more).

Computational research can be intimidating because there are so many programs to choose from, and it's hard to mix-and-match them for your specific project. Simmate aims to be the glue between all these different programs, databases, and utilities. We do the heavy lifting and explain these other programs to you along the way.

Even if you consider yourself an experimentalist and have little-to-no coding experience, Simmate's barrier to entry is built to be as low as possible. Our web interface can generate property predictions with a single mouse click. And for learning how to code, we wrote our tutorials and documentation for those that have never used python before. 

At the other end of the spectrum, we provide an extremely powerful toolbox and API for experts. Those familiar with the field can view Simmate as an alternative to the [Materials Project](https://materialsproject.org/) stack ([Atomate](https://github.com/hackingmaterials/atomate), [PyMatGen](https://github.com/materialsproject/pymatgen), [MatMiner](https://github.com/hackingmaterials/matminer), and [more](https://matsci.org/)), where we operate under a very different coding philosphy. **Here, usability and readability are our top priorities.** We therefore distribute Simmate as an "all-in-one" package rather than many separate programs. This includes a core material science toolkit, workflow management, database orm, and a website interface. **Simmate also focuses heavily on cloud-based storage**, which enables large scale collaborations and avoids researchers repeating calculations. To learn more about the different design choices made in Simmate compared to competing codes, read through our [comparisons and benchmarks page](https://github.com/jacksund/simmate/tree/main/benchmarks).

--------------------------------------------------------------------------------

## A Sneak-Peak of Features

Again, take a look at [our main website](https://simmate.org/) if you'd like to see the end-result of what Simmate has to offer. There are many more functions and utilities once you download Simmate, so this section showcases a few of those features.


### Prebuilt Workflows
All of the most common material properties have workflows ready to go. These range from simple XRD pattern predictions to intensive dynamic simulations. Simmate also builds off of [Prefect](https://github.com/PrefectHQ/prefect) for orchestrating and managing workflows. This means that it's up to you whether to run jobs via (i) an advanced user-interface, (ii) the command-line, or (iii) in custom python scripts:

=== "yaml"
    ``` yaml
    # in example.yaml
    workflow_name: relaxation.vasp.matproj
    structure: NaCl.cif
    command: mpirun -n 8 vasp_std > vasp.out
    ```

    ``` bash
    simmate workflows run example.yaml
    ```

=== "command line"
    ``` bash
    simmate workflows run relaxation.vasp.matproj --structure NaCl.cif
    ```

=== "toml"
    ``` toml
    # in example.toml
    workflow_name = "relaxation.vasp.matproj"
    structure = "NaCl.cif"
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```

    ``` bash
    simmate workflows run example.yaml
    ```

=== "python"
    ``` python
    from simmate.workflows.relaxation import Relaxation__Vasp__Matproj as workflow
    
    state = workflow.run(structure="NaCl.cif")
    result = state.result()
    ```


### Full-Feature Database
Using all the data on our official site along with your own private data, you can take advantage of Simmate's extremely powerful database that is built off of [Django ORM](https://github.com/django/django). Simmate also brings together third-party databases and their data -- including those like the COD, Materials Project, JARVIS, and others. With so much data, being able to easily download and navigate it is critical:

```python
from simmate.database import connect # (1)
from simmate.database.third_parties import MatprojStructure

# EXAMPLE 1
structures = MatprojStructure.objects.filter(nsites__lt=6).all() # (2)

# EXAMPLE 2
structures = MatprojStructure.objects.filter(  # (3)
    nsites__gte=3,
    energy__isnull=False,
    density__range=(1,5),
    elements__icontains='"C"',
    spacegroup__number=167,
).all()

# Quickly convert to excel, a pandas dataframe, or toolkit structures.
df = structures.to_dataframe()
structures = structures.to_toolkit()
```

1. Be sure to follow the database tutorial where we build our initial database with the command `simmate database reset`
2. all structures that have less than 6 sites in their unitcell
3. This filter to... greater or equal to 3 sites, the structure DOES have an energy, density is between 1 and 5, the structure includes the element Carbon, and the spacegroup number is 167


### Utilities & Toolbox 
A lot of times in research, a new method is needed to analyze a structure, so a prebuilt workflow won't exist for you yet. Here, you'll need common functions ready to go (such as grabbing the volume of a crystal or running symmetry analysis). Our toolkit functions and classes largely inherit from [PyMatGen](https://github.com/materialsproject/pymatgen), which gives you a wide variety of functions to use:

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


### Scalable to Clusters
At the beginning of a project, you may want to write and run code on a single computer and single core. But as you run into some intense calculations, you may want to use all of your CPU and GPU to run calculations. At the extreme, some projects require thousands of computers across numerous locations, including university clusters (using SLURM or PBS) and cloud computing (using Kubernetes and Docker). Simmate can meet all of these needs thanks to integration with a custom `SimmateExecutor` (the default), [Dask](https://github.com/dask/dask), and/or [Prefect](https://github.com/PrefectHQ/prefect):

=== "schedule jobs"
    ```python
    state = workflow.run_cloud(structure="NaCl.cif")  # (1)
    result = state.result()  # (2)
    ```

    1. On your local computer, schedule your workflow run. This is as easy as replacing "run" with "run_cloud". This returns a "future-like" object.
    2. Calling result will wait until the job completes and grab the result! Note, the job won't run until you start a worker that is connected to the same database (see command below)

=== "add remote resources"
    ``` bash
    simmate engine start-worker  # (1)
    ```

    1. In a separate terminal or even on a remote HPC cluster, you can start a worker that will start running any scheduled jobs

--------------------------------------------------------------------------------

## Need help?

Post your question [here in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 

--------------------------------------------------------------------------------

## Extra resources

- [Requesting a new feature](https://github.com/jacksund/simmate/discussions/categories/ideas)
- [Exploring alternatives to Simmate](https://github.com/jacksund/simmate/tree/main/benchmarks)
- [Citing Simmate](https://doi.org/10.21105/joss.04364)
