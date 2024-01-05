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

This website is your go-to resource for all our tutorials and guides. Before diving in, you might want to explore:

- Our main website at [simmate.org](https://simmate.org/)
- Our source code at [github.com/jacksund/simmate](https://github.com/jacksund/simmate)

--------------------------------------------------------------------------------

## What is Simmate?

Simmate, or the Simulated Materials Ecosystem, is a comprehensive toolbox and framework designed for computational materials research. It allows you to explore various crystal databases, predict new materials, and easily calculate properties such as electronic, elastic, thermodynamic, and more.

Computational research can be intimidating because there are so many programs to choose from, and it's challenging to select and combine them for your specific project. Simmate is designed to bridge this gap, acting as the adhesive between these diverse programs, databases, and utilities. We take on the heavy lifting and provide clear explanations of these programs along the way.

Simmate is designed to be accessible to all, including experimentalists with minimal coding experience. Our user-friendly web interface can generate property predictions with a single mouse click. For those interested in learning to code, our tutorials and documentation are written with beginners in mind.

At the other end of the spectrum, we provide an extremely powerful toolbox and API for experts. Those familiar with the field can view Simmate as an alternative to the [Materials Project](https://materialsproject.org/) stack ([Atomate](https://github.com/hackingmaterials/atomate), [PyMatGen](https://github.com/materialsproject/pymatgen), [MatMiner](https://github.com/hackingmaterials/matminer), and [more](https://matsci.org/)), where we operate under a distinct coding philosophy. **Our top priorities are usability and readability.** We distribute Simmate as an "all-in-one" package, including a core material science toolkit, workflow management, database ORM, and a website interface. **Simmate also emphasizes cloud-based storage**, facilitating large scale collaborations and preventing redundant calculations. To understand more about the unique design choices in Simmate compared to other codes, visit our [comparisons and benchmarks page](https://github.com/jacksund/simmate/tree/main/benchmarks).

--------------------------------------------------------------------------------

## A Sneak-Peak of Features

Visit [our main website](https://simmate.org/) to see the full range of what Simmate offers. This section highlights a few features available once you download Simmate.


### Prebuilt Workflows
Simmate comes with ready-to-use workflows for most common material properties, ranging from simple XRD pattern predictions to intensive dynamic simulations. Simmate builds on [Prefect](https://github.com/PrefectHQ/prefect) for orchestrating and managing workflows, giving you the flexibility to run jobs via an advanced user-interface, the command-line, or in custom python scripts:

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
Simmate's powerful database, built on [Django ORM](https://github.com/django/django), allows you to leverage all the data on our official site along with your private data. Simmate also integrates third-party databases and their data, including COD, Materials Project, JARVIS, and more. With such a wealth of data, easy navigation and download capabilities are crucial:

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

1. Follow the database tutorial to build our initial database with the command `simmate database reset`
2. Retrieves all structures with less than 6 sites in their unit cell
3. This filter retrieves structures with: greater or equal to 3 sites, an energy value, density between 1 and 5, the element Carbon, and spacegroup number 167


### Utilities & Toolbox 
In research, you often need a new method to analyze a structure, and a prebuilt workflow may not exist. Simmate provides common functions ready to use, such as calculating the volume of a crystal or running symmetry analysis. Our toolkit functions and classes largely inherit from [PyMatGen](https://github.com/materialsproject/pymatgen), offering a wide variety of functions:

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
Simmate is designed to scale with your project. Whether you're working on a single computer or need to use all your CPU and GPU for intense calculations, Simmate has you covered. For large-scale projects requiring thousands of computers across multiple locations, including university clusters (using SLURM or PBS) and cloud computing (using Kubernetes and Docker), Simmate integrates with a custom `SimmateExecutor` (the default), [Dask](https://github.com/dask/dask), and/or [Prefect](https://github.com/PrefectHQ/prefect):

=== "schedule jobs"
    ```python
    state = workflow.run_cloud(structure="NaCl.cif")  # (1)
    result = state.result()  # (2)
    ```

    1. On your local computer, schedule your workflow run. This is as easy as replacing "run" with "run_cloud". This returns a "future-like" object.
    2. Calling result will wait until the job completes and grab the result! Note, the job won't run until you start a worker that is connected to the same database

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