# Accessing your database and others

In tutorial 2, we setup our database and added a structure+calcution to it. Now, we want to add massive databases that already exist (such as the [Materials Project](https://materialsproject.org/)) and explore this data efficiently.

## The quick version

1. Visit Simmate's download page at simmate.org/downloads/. Here you will see various compressed archives that can be downloaded and used as you wish. But rather than manually loading each of these files, let's use Simmate's python client to do this.
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
