# Accessing your database and others

To review key concepts up until this point...
- In tutorial 2, we setup our database and added calcution results to it.
- In tutorials 3, we learned about python classes, and in particular, the importance of the `Structure` class.
- In tutorial 4, we learned how to explore the documentation and use new classes.

Now, we want to bring these ideas together in order to expolore our database (as well as data from third-parties). 

## The quick version

1. Make sure you've initialized your database. This was done in tutorial 2 with the command `simmate database reset`.
2. Go to the `simmate.database` module to view all available tables. Note, many of the tables `local_calculations` are actually defined in their corresponding `calculators` module.
3. The table for Tutorial 1's results are located in the `MITRelaxation` datatable class, which can be loaded via either of these options:
```python
# OPTION 1
from simmate.shortcuts import setup  # this connects to our database
from simmate.database.local_calculations.relaxation import MITRelaxation

# OPTION 2 (slower but recommended for convenience)
from simmate.workflows.all import relaxation_mit
results = relaxation_mit.results_table  # results here is the same thing as MITRelaxation above
```
4. View all the possible table columns with `MITRelaxation.list_all_columns()`
5. View the full table as pandas dataframe with `MITRelaxation.objects.to_dataframe()`
6. Filter results using [django-based queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/). For example:
```python
filtered_results = MITRelaxation.objects.filter(formula_reduced="NaCl", nsites__lte=2).all()
```
7. Convert the final structure from a database object (aka `DatabaseStructure`) to a structure (aka `ToolkitStructure`) object.
```python
single_relaxation = MITRelaxation.objects.filter(formula_reduced="NaCl", nsites__lte=2).first()
nacl_structure = single_relaxation.structure_final.to_pymatgen()
```
8. For third-party data (like [Material Project](https://materialsproject.org/), [AFLOW](http://aflowlib.org/), [COD](http://www.crystallography.net/cod/), etc.) load the database table and then request to download all the available data:
```python
from simmate.shortcuts import setup  # this connects to our database
from simmate.database.third_parties.jarvis import JarvisStructure

# This only needs to ran once
JarvisStructure.load_data_archive()

# now explore the data (only the first 150 structures here)
first_150_rows = JarvisStructure.objects.all()[:150]
dataframe = first_150_rows.to_dataframe()
```
> :warning: To protect our servers, you can only call `load_data_archive()` a few times per month. Don't overuse this feature.


## The full tutorial

This tutorial will include...
- TODO

2. Jump to the `simmate.databse` module where we can see a bunch of other modules. This each file here represents a database table for us to use. Let's start by finding the table for Materials Project and loading data into it! The datatable python class is located in `simmate.databse.third_parties.materials_project`.
3. Here we have a database table name `MaterialsProjectStructure` that inherits all columns from a generic `Structure` database table. This means the `MaterialsProjectStructure` has the following columns for its data:
```python
# these columns you can see directly in the MaterialsProjectStructure class
final_energy
final_energy_per_atom
formation_energy_per_atom
energy_above_hull
band_gap

# these columns come from the Structure class that is inherited
structure_string
nsites
nelements
chemical_system
density
molar_volume
formula_full
formula_reduced
formula_anonymous
spacegroup --> See below!

# the `spacegroup` column links to another table which has these columns
number
symbol
crystal_system
point_group
```
4. We already built these databases using the `simmate database reset` command in tutorial 1. Now we can use python to load >140,000 structures from the Materials Project into it:
```python
# first we need to connect to our database
from simmate.shortcuts import setup

# now we can import the datatable we want
from simmate.database.third_parties.material_project import MaterialsProjectStructure

# And request to download the data for it
MaterialsProjectStructure.load_data_archive()
```
> :warning: To protect our servers, you are only allowed to download an archive **once every 5 minutes** and **30 times per month**. If you exceed these limits, you'll have to make a request with a new account.

6. The `load_data_archive` method only needs to be ran once. You then have the everything in your database forever!
7. To explore structures, we use all the columns above along with [Django's query language](https://docs.djangoproject.com/en/3.2/topics/db/queries/):
```python
# Here are some examples of querying the Materials Project database for specific structures
from simmate.database.third_party.materials_project import MaterialsProjectStructure

# EXAMPLE 1: all structures that have less than 6 sites in their unitcell
structures = MaterialsProjectStructure.objects.filter(nsites__lt=6).all()

# EXAMPLE 2: all MoS2 structures that are less than 10g/A^3 and have a bulk
# modulus greater than 0.5
structures = MaterialsProjectStructure.objects.filter(
   formula="MoS2",
   density__lt=10,
   elastic__bulk_modulus__gt=0.5,
).all()
```
8. You can try downloading other datatables as well. All tables have the `load_data_archive` method, so you can go ahead and load other third party databases quickly.
9. Navigating your own calculation data works in the same way:
```python
# first we need to connect to our database
from simmate.shortcuts import setup

# now we can import the datatables we want
from simmate.database.local_calculations.relaxation.mit import MITRelaxation, MITRelaxationStructure

# EXAMPLE 1: grab all final structures and convert to a list of pymatgen objects
final_structures = MITRelaxationStructure.objects.filter(relaxations_as_final__isnull=True).all()
pymatgen_structures = final_structures.to_pymatgen()

# EXAMPLE 2: grab the very first relaxation and then all the ionic steps related to it
relaxation = MITRelaxation.objects.first()
ionic_step_structures = relaxation.structures
```

## The full tutorial

This tutorial will include...
- TODO
