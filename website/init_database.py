# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------

"""

This script creates my initial database from a specified Materials Project query.
It also saves the initial database to csv files for reference.

Setup your database before running this script. You do this in the command prompt by
running...
    python .\manage.py makemigrations exam;
    python .\manage.py migrate;

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

# Querying MP database and saving to csv

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

# convert the query to a pandas dataframe
import pandas
df = pandas.DataFrame.from_dict(output)

# convert the structure column to json for storage
df.structure = df.structure.apply(lambda structure: structure.to_json())

# save the dataframe to a csv file
df.to_csv('db_initial.csv', index=False) # I don't save the index column

#--------------------------------------------------------------------------------------

# Loading a csv file

# Load dataframe from csv file
df = pandas.read_csv('db_initial.csv') # wStructDicts

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
df.to_csv('db_santized.csv', index=False) # I don't save the index column

#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------

# Using Django ORM

# this line sets up the django enviornment
import manageinpython

# import models to make a query
from django.contrib.auth.models import User
users = User.objects.all()
# or
from exam.models import Question
questions = Question.objects.filter(answer_type='MC')

question = questions[0]

# Or outside of the django setup
#!!! NOT WORKING AT THE MOMENT
# https://stackoverflow.com/questions/2180415/using-django-database-layer-outside-of-django

#--------------------------------------------------------------------------------------

# Directions on how to see what the raw SQL command looks like:
# https://docs.djangoproject.com/en/3.1/faq/models/#how-can-i-see-the-raw-sql-queries-django-is-running

from django.db import connection
queries = connection.queries

# if you have a queryset (output from a django query) you can do this instead:
query = users.query.__str__()

#--------------------------------------------------------------------------------------

# Using raw SQL for SQLite3 file
# For testing with sqlite3: https://docs.python.org/3/library/sqlite3.html

# connect to database
import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# write out your command in raw SQL
query = 'SELECT * FROM exam_question LIMIT 2'

# make the query against the database
cursor.execute(query)
output = cursor.fetchall()
conn.commit() # if changes made

# if you want column names, this is how you grab them
names = [description[0] for description in cursor.description]

# close connections
cursor.close()
conn.close()

#--------------------------------------------------------------------------------------

# Using Prefect Tasks
# For methods sqlite3 and many other db types, it's useful to start with Prefect Tasks
# https://docs.prefect.io/api/latest/tasks/sqlite.html

from prefect.tasks.database.sqlite import SQLiteQuery

task = SQLiteQuery(
    db='db.sqlite3',
    query = 'SELECT * FROM exam_question LIMIT 2',
    )

output = task.run()

#--------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------

""" EXAMPLE OF MAKING A USER PROFILE """

from django.contrib.auth.models import User

# alternatively I can use User.objects.create_user which will also hanlde making the password
user = User(username = 'jacksund',
                email = 'jacksund' + '@live.unc.edu')
# we can't give the password above because it needs to pass through the hash
user.set_password('yeet123') 
user.save()

#--------------------------------------------------------------------------------------

""" EXAMPLE OF MAKING AN EXAM """

from exam.models import Exam
import datetime
import pytz

# create the exam
exam = Exam(name = 'Chem 102: 2020 Spring Final',
            date = datetime.datetime(year = 2020,
                                     month = 5,
                                     day = 5,
                                     hour = 13,
                                     minute = 30,
                                     tzinfo = pytz.utc), # this passes timezone info, but I need to understand this better...
            time_limit = datetime.timedelta(hours=2),)
exam.save()

# add users and instructors to the exam via the .add() method
exam.students.add(user)
#!!! do I need to save the exam again? I don't think so but I should doublecheck this

#--------------------------------------------------------------------------------------

# from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

# dpf = DistinctPathFinder(
#     structure = structure,
#     migrating_specie = 'Li',
#     max_path_length = 10, 
#     symprec = 0.1,
#     perc_mode = None,
#     )

# paths = dpf.get_paths()

