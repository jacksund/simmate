# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------

"""

Going through all structures in our SQL databse, we use pymatgen-diffusion to identify
all unique paths for Fluorine diffusion here.

"""

#--------------------------------------------------------------------------------------

# Load the Structure sql table, convert to a Pandas dataframe, and init pymatgen
# Structure objects for the structure column

# this line sets up the django enviornment
#!!! switch to absolute import path in the future
import manageinpython

# import the model and grab all of the rows
#!!! switch to absolute import path in the future
from diffusion.models import Structure
structures = Structure.objects.all()

# convert to a pandas dataframe
import pandas
df = pandas.DataFrame.from_records(structures.values())

# change structure column from a json string to a dictionary
import json
df.structure = df.structure.apply(json.loads)
# change structure column from dictionary to pymatgen structure object
from pymatgen.core import Structure
df.structure = df.structure.apply(Structure.from_dict)

#--------------------------------------------------------------------------------------

#!!! test structure
test = df.sample(1)
structure = test.structure.values[0]
structure_id = test.id.values[0]

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

dpf = DistinctPathFinder(
    structure = structure,
    migrating_specie = 'F',
    max_path_length = 2.6, 
    symprec = 0.1,
    perc_mode = None,
    )

paths = dpf.get_paths()

outputs = []

for path_index, path in enumerate(paths): 
    # append the result dictionary to an outputs list
    output = dict(
        structure_id = structure_id,
        index = path_index,
        distance = path.length,
        isite = path.isite.frac_coords,
        msite = path.msite.frac_coords,
        esite = path.esite.frac_coords,
        )
    outputs.append(output)

#--------------------------------------------------------------------------------------

from diffusion.models import Pathway

#--------------------------------------------------------------------------------------

artist = Artist.objects.get(id=1)  
newMp3 = Mp3(title="sth", artist=artist)

#--------------------------------------------------------------------------------------

