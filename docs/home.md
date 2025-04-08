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


## Before you begin

This website is your go-to resource for all our tutorials and guides. Before diving in, you might want to explore:

- Our main website at [simmate.org](https://simmate.org/)
- Our source code at [github.com/jacksund/simmate](https://github.com/jacksund/simmate)

## What is Simmate?

Simmate is a full-stack framework for chemistry research. It helps you calculate properties and explore third-party databases for both for molecular and crystalline systems. For experts, it also provides a toolbox to build out your own chemistry applications.

The computational side of chemistry research can be intimidating because there are so many programs to choose from, and it's challenging to select and combine them for your specific project. Simmate aims to bridge this gap, acting as a link between the many diverse programs, databases, and utilities out there. Third-party datasets and tools are ingetrated into Simmate as "apps", where there is a growing list of [supported software and databases](/apps/overview.md).

We also provide an extremely powerful toolbox and API for experts. Our top priorities are usability and readability, so we distribute Simmate as an "all-in-one" package. This includes a core chemical toolkit, workflow management, database ORM, and a website interface.

## A Sneak-Peak of Features

### Prebuilt Workflows
Simmate comes with ready-to-use workflows for most common calculated properties, ranging from simple XRD pattern prediction to intensive dynamic simulations. All workflows can be submitted via a website user-interface, the command-line, or custom python scripts:

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
    simmate workflows run-quick relaxation.vasp.matproj --structure NaCl.cif
    ```

=== "toml"
    ``` toml
    # in example.toml
    workflow_name = "relaxation.vasp.matproj"
    structure = "NaCl.cif"
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```

    ``` bash
    simmate workflows run example.toml
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("relaxation.vasp.matproj")
    status = workflow.run(structure="NaCl.cif")
    result = status.result()
    ```

=== "website"
    ``` url
    https://simmate.org/workflows/static-energy/vasp/matproj/submit
    ```

### Scalable Orchestration
Simmate can easily scale along with your project, whether you're on a single computer or across thousands of machines. It supports various setups, including university clusters with SLURM or PBS, and cloud platforms using Kubernetes and Docker.

=== "create workflow"
    ```python
    from simmate.engine import workflow

    @workflow
    def hello(name, **kwargs):  # (1)
        print(f"Hello {name}!")
        print(f"Extra parameters configured for you: {kwargs}")
    ```

    1. We always use `**kwargs` because Simmate automatically provides extra variables at runtime, such as `run_id` and `directory`.

=== "schedule jobs"
    ```python
    state = workflow.run_cloud(name="Jack")  # (1)
    result = state.result()  # (2)
    ```

    1. On your local computer, schedule your workflow run. This returns a "future-like" object.
    2. This will wait until the job completes and return the result. Note, the job won't run until you start a worker that is connected to the same database

=== "add remote resources"
    ``` bash
    simmate engine start-worker  # (1)
    ```

    1. In a separate terminal or even on a remote HPC cluster, you can start a worker that will start running any scheduled jobs in your database.


### Full-Feature Database
Simmate's database can manage your perosnal data while also integrating with third-party databases such as COD, Materials Project, JARVIS, and others. It automatically constructs tables with common data types by including a wide range of standard columns. You can then access this data through a web interface, REST API, SQL, or Python ORM:

=== "python"

    ```python
    from simmate.database import connect # (1)
    from simmate.apps.materials_project.models import MatprojStructure

    # Query the database
    structures = MatprojStructure.objects.filter(  # (2)
        nsites__gte=3,
        energy__isnull=False,
        density__range=(1,5),
        elements__icontains='"C"',
        spacegroup__number=167,
    ).all()

    # Convert to excel, a pandas dataframe, toolkit structures, etc.
    df = structures.to_dataframe()
    structures = structures.to_toolkit()
    ```

    1. Follow the database tutorial to build our initial database with the command `simmate database reset`
    2. This filter retrieves structures with: greater or equal to 3 sites, an energy value, density between 1 and 5, the element Carbon, and spacegroup number 167

=== "SQL"
    ``` postgres
    SELECT *
    FROM materials_project__structures
    WHERE nsites >= 3
      AND energy IS NOT NULL
      AND density BETWEEN 1 AND 5
      AND elements ILIKE '%"C"%'
      AND spacegroup_number = 167;
    ```

=== "REST API"
    ``` url
    https://simmate.org/third-parties/MatprojStructure/?format=json
    ```

=== "website"
    ``` url
    https://simmate.org/third-parties/MatprojStructure/
    ```

### Beginner-Friendly Toolkit
Simmate includes a `toolkit` that builds off popular packages in the chemistry community, specifically [`rdkit`](https://www.rdkit.org/) for molecular systems and [`pymatgen`](https://pymatgen.org/) for crystalline systems. The end result is a toolkit that is "batteries-included" and very powerful for rapidly prototyping analyses. Here is an eample script that is straightforward & clean with Simmate's toolkit, but less intuitive & Pythonic for others:

=== "simmate-toolkit"
    ``` python
    from simmate.toolkit import Molecule

    # STEP 1
    molecules = Molecule.from_sdf_file("example.sdf")

    # STEP 2
    molecules_filtered = []
    for molecule in molecules:
        if molecule.num_stereocenters > 3:
            continue
        if molecule.num_atoms_heavy > 30:
            continue
        if "Na" in molecule.elements:
            continue
        molecules_filtered.append(molecule)

    # STEP 3
    inchi_keys = [m.to_inchi_key() for m in molecules_filtered]
    ```

=== "rdkit"
    ``` python
    from rdkit import Chem
    from rdkit.Chem import FindMolChiralCenters, Descriptors

    # STEP 1
    molecules = []
    with Chem.SDMolSupplier("example.sdf") as supplier:
    for molecule in supplier:
        if mol is None:
            continue
        molecules.append(molecule)

    # STEP 2
    molecules_filtered = []
    for molecule in molecules:

        chiral_centers = FindMolChiralCenters(
            molecule,
            force=True,
            includeUnassigned=True,
            useLegacyImplementation=False,
        )
        if len(chiral_centers) > 3:
            continue
        
        nheavy = Descriptors.HeavyAtomCount(molecule)
        if nheavy > 30:
            continue

        has_na = False  # false until proven otherwise
        for atom in molecule.GetAtoms():
            if atom.GetSymbol() == "Na":
                has_na = True
                break
        if has_na:
            continue

        molecules_filtered.append(molecule)

    # STEP 3
    inchi_keys = [Chem.MolToInchiKey(m) for m in molecules_filtered]
    ```

=== "oe-toolkit"
    ``` python
    from openeye import oechem
    from openeye import oeiupac
    
    # STEP 1
    molecules = []
    with oechem.oemolistream("example.sdf") as ifs:
        for mol in ifs.GetOEMols():
            if mol is None:
                continue
            molecules.append(mol)
    
    # STEP 2
    molecules_filtered = []
    for mol in molecules:
    
        stereo_count = sum(1 for atom in mol.GetAtoms() if atom.IsChiral())
        if stereo_count > 3:
            continue
    
        heavy_atom_count = sum(
            1 for atom in mol.GetAtoms() if atom.GetAtomicNum() > 1
        )
        if heavy_atom_count > 30:
            continue
    
        has_na = any(atom.GetAtomicNum() == 11 for atom in mol.GetAtoms())
        if has_na:
            continue
    
        molecules_filtered.append(mol)
    
    # STEP 3
    inchi_keys = [oeiupac.OECreateInChIKey(m) for m in molecules_filtered]
    ```

## Need help?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 
