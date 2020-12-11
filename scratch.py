# -*- coding: utf-8 -*-

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