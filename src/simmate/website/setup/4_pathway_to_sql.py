# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------

"""

This script creates my initial csv database from a specified Materials Project query.
It also saves the initial database to csv for reference.

Setup your database before running this script. You do this in the command prompt by
running...
    python manage.py makemigrations diffusion;
    python manage.py migrate;

IMPORTANT: For the working directory (in Spyder) I set to /simmate/website, which 
is one directory up from this one. I did this because I don't want to mess with 
django's relative imports yet, and I really only need to run this script once.

"""

#--------------------------------------------------------------------------------------

# Connecting to MP database

# Connect with personal API key
from pymatgen import MPRester
mpr = MPRester("2Tg7uUvaTAPHJQXl")

# For reference, grab the database version
db_version = mpr.get_database_version()
# '2020_09_08'

#--------------------------------------------------------------------------------------

# Querying MP database

# Filtering criteria for which structures to look at in the Materials Project
# Catagories such as 'elements' that we can filter off of are listed here:
#       https://github.com/materialsproject/mapidoc
# Conditions such as $in or $exists that we filter based on are listed here:
#       https://docs.mongodb.com/manual/reference/operator/query/
criteria={
    "elements": {
        "$all": ["F"],
        }
    }

# For the filtered structures, which properties I want to grab.
# All properties that we can grab are listed here:
#       https://github.com/materialsproject/mapidoc
properties=[
    "material_id",
    "nsites", 
    "pretty_formula",
    "final_energy",
    "final_energy_per_atom",
    "formation_energy_per_atom",
    "e_above_hull",
    "density",
    "structure",
    ]

# make the query to Materials Project
output = mpr.query(criteria, properties)

#--------------------------------------------------------------------------------------

# Save this initial query data to a csv file for reference

# convert the query to a pandas dataframe
import pandas
df = pandas.DataFrame.from_dict(output)

# convert the structure column to json for storage
df.structure = df.structure.apply(lambda structure: structure.to_json())

# save the dataframe to a csv file
# I don't save the index column
df.to_csv('setup/db_initial.csv', index=False)

#--------------------------------------------------------------------------------------

# Loading a csv file -- This section really doesn't need to be done. But it ensures
# that loading works, and serves as a reference on how to do it properly

# Load dataframe from csv file
df = pandas.read_csv('setup/db_initial.csv') # wStructDicts

# change structure column from a json string to a dictionary
import json
df.structure = df.structure.apply(json.loads)
# change structure column from dictionary to pymatgen structure object
from pymatgen.core import Structure
df.structure = df.structure.apply(Structure.from_dict)

#--------------------------------------------------------------------------------------

# Run symmetry and "sanitization" on all structures and save to csv

# Make sure we have the primitive unitcell first
# We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
# built-in Structure.get_primitive_structure function.
# df.structure = df.structure.apply(lambda structure: structure.get_primitive_structure(0.1)) # Default tol is 0.25
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
df.structure = df.structure.apply(lambda structure: SpacegroupAnalyzer(structure, 0.1).find_primitive()) # Default tol is 0.01

# Grab each structure and convert it to a "sanitized" version.
# This includes... 
    # (i) an LLL reduction
    # (ii) transforming all coords to within the unitcell
    # (iii) sorting elements by electronegativity
df.structure = df.structure.apply(lambda structure: structure.copy(sanitize=True))

# number of sites may have decreased when we switched to the primitive structure so we
# need to update the value here
df.nsites = df.structure.apply(lambda structure: structure.num_sites)

# convert the structure column to json for storage
df.structure = df.structure.apply(lambda structure: structure.to_json())

# save the dataframe to a csv file
# I don't save the index column
df.to_csv('setup/db_santized.csv', index=False)

#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------

# Now save the dataframe to our sql database using Django ORM
# The script will fail here if you didn't setup your db yet 
# (see comment at the top of the file)

# this line sets up the django enviornment
#!!! switch to absolute import path in the future
import manageinpython

# import the model so we can start saving to the table
#!!! switch to absolute import path in the future
from diffusion.models import Structure

# iterate through the pandas dataframe and save each row to the sql database
# note that the structure column is already converted to a json string
#!!! This currently very slow, but I can speed it up a number of ways:
    # converting df to numpy before iterating (use df.values)
    # using a faster sql database such as postgres
    # committing all saves at once to sql (use with transaction.atomic())
for row in df.itertuples():
    new_structure = Structure(
        material_id = row.material_id,
        nsites = row.nsites,
        pretty_formula = row.pretty_formula,
        final_energy = row.final_energy,
        final_energy_per_atom = row.final_energy_per_atom,
        formation_energy_per_atom = row.formation_energy_per_atom,
        e_above_hull = row.e_above_hull,
        density = row.density,
        structure = row.structure
        )
    new_structure.save()

#--------------------------------------------------------------------------------------


