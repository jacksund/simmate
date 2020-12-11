# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------

"""

Using the csv file made previously, this script moves the data into the SQL database.

Setup your database before running this script. You do this in the command prompt by
running...
    python manage.py makemigrations diffusion;
    python manage.py migrate;

IMPORTANT: For the working directory (in Spyder) I set to /fhahtda/website, which 
is one directory up from this one. I did this because I don't want to mess with 
django's relative imports yet, and I really only need to run this script once.

"""

#--------------------------------------------------------------------------------------

# Loading the csv file into Pandas dataframe and init pymatgen structure objects

# Load dataframe from csv file
df = pandas.read_csv('setup/db_santized.csv') # wStructDicts

# change structure column from a json string to a dictionary
import json
df.structure = df.structure.apply(json.loads)
# change structure column from dictionary to pymatgen structure object
from pymatgen.core import Structure
df.structure = df.structure.apply(Structure.from_dict)

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
