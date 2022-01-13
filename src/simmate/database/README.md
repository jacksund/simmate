The Simmate Database
--------------------

This module hosts everything for defining and interacting with your database.


Various database actions
------------------------

Viewing the raw SQL commands that are ran:
```python
# https://docs.djangoproject.com/en/3.1/faq/models/#how-can-i-see-the-raw-sql-queries-django-is-running

from django.db import connection
queries = connection.queries

# if you have a queryset (output from a django query) you can do this instead:
query = users.query.__str__()
```


Running raw SQL commands directly against a file (not recommended!):
```python
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

# close connections
cursor.close()
conn.close()
```


Using Prefect to run raw SQL query against a file:
```python
# Using Prefect Tasks
# For methods sqlite3 and many other db types, it's useful to start with Prefect Tasks
# https://docs.prefect.io/api/latest/tasks/sqlite.html

from prefect.tasks.database.sqlite import SQLiteQuery

task = SQLiteQuery(
    db='db.sqlite3',
    query = 'SELECT * FROM exam_question LIMIT 2',
    )

output = task.run()
```


Example of making a user profile that properly uses hashing for storage:
```python
from django.contrib.auth.models import User

# alternatively I can use User.objects.create_user which will also hanlde making the password
user = User(username = 'jacksund',
                email = 'jacksund' + '@live.unc.edu')
# we can't give the password above because it needs to pass through the hash
user.set_password('yeet123') 
user.save()
```


Example of making an object with time-specific information:
```python
from example import Exam
import datetime
import pytz

exam = Exam(
    name="Chem 102: 2020 Spring Final",
    date=datetime.datetime(
        year=2020,
        month=5,
        day=5,
        hour=13,
        minute=30,
        tzinfo=pytz.utc,
    ),
    time_limit=datetime.timedelta(hours=2),
)
exam.save()
```
