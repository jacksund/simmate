This module hosts everything for SQL-type database access. Right now it's just the ORM, but I may make submodules of 'orm', 'api', and 'util' in the future.

It is likely to be a common task for users to convert data from SQL to CSV. To do this, we'd really take a django QuerySet --> convert it to a Pandas dataframe --> and then write the CSV file. There is a python package written for this (here)[https://github.com/chrisdev/django-pandas] but because it's really just one file that we'd use, it may be worth rewritting. It doesn't look like it handles relationship columns the way I'd like, as storing the related primary key is sufficient.


If I ever need to look at the raw sql being executed for optimization...
```python
# Directions on how to see what the raw SQL command looks like:
# https://docs.djangoproject.com/en/3.1/faq/models/#how-can-i-see-the-raw-sql-queries-django-is-running

from django.db import connection
queries = connection.queries

# if you have a queryset (output from a django query) you can do this instead:
query = users.query.__str__()
```


Running raw SQL commands directly against a file:
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

# if you want column names, this is how you grab them
names = [description[0] for description in cursor.description]

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


Example of making an object with time-specific information and also adding another
model to it's list of foreign keys:
```python
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
```







"""

Every base model class has the sections shown below. These are simply to organize the
code and make it easier to read:

Base Info
    These fields are the absolute minimum required for the object and can be
    considered the object's raw data.

Query-helper Info
    These fields aren't required but exist simply to help with common query
    functions. For example, a structure's volume can be calculated using the
    base info fields, but it helps to have this data in a separate column to
    improve common query efficiencies at the cost of a larger database.

Relationships
    These fields point to other models that contain related data. For example,
    a single structure may be linked to calculations in several other tables.
    The relationship between a structure and it's calculations can be described
    in this section. Note that the code establishing the relationship only exists
    in one of the models -- so we simply add a comment in the other's section.
    TYPES OF RELATIONSHIPS:
        ManyToMany - place field in either but not both
        ManyToOne (ForeignKey) - place field in the many
        OneToOne - place field in the one that has extra features

Properties
    In a few cases, you may want to add a convience attribute to a model. However,
    in the majority of cases, you'll want to convert the model to some other
    class first which has all of the properties you need. We separate classes
    in this way for performance and clarity. This also allows our core and
    database to be separate and thus modular.

Model Methods
    These are convience functions added onto the model. For example, it's useful
    to have a method to quickly convert a model Structure (so an object representing
    a row in a database) to a pymatgen Structure (a really powerful python object)

For website compatibility
    This contains the extra metadata and code needed to get the class to work
    with Django and other models properly.

"""

"""
TODO: these are ideas for other models that I still need to write. Some are based
off of the Materials Project MapiDoc and will likely change a lot.

NEW: There is now "EMMET" which is a good way to model our database off of.
        https://github.com/materialsproject/emmet

StructureCluster (or MatchingStructures)
    This is maps to a given structure in primary structure table and links that
    structures relations to all other databases. For example, it will map to the
    list of mp-ids and icsd-ids that match the structure within a given tolerance.
    This subclasses Calculation because structure matching takes a really long time
    and even needs to be reran on occasion.
    ICSD, MP, AFLOW, JARVIS, etc...

EnergyCalculation
    final_energy
    e_above_hull
    final_energy_per_atom
    formation_energy_per_atom

    # for relaxation
    delta_volume(%)

    # settings (may be properties!)
    encut
    nkpts --> kpt density
    psudeopotential
        functional(PBE)
        label(Y_sv)
        pot_type(PAW)
    run_type(GGA,GGAU,HF)
    is_hubbard

Spacegroup
    number
    crystal_system
    hall
    number
    pointgroup
    source
    symbol

BandStructure + DOS
    band_gap
    is_direct
    type
    efermi

Dielectric
    e_electronic
    e_total
    n
    poly_electronic
    poly_total

Elasticity + ElesticityThirdOrder
    (G=shear; K=bulk)
    G_Reuss
    G_VRH
    G_Voigt
    G_Voight_Reuss_Hill
    K_Reuss
    K_VRH
    K_Voight
    K_Voight_Reuss_Hill
    compliance_tensor
    elastic_anisotropy
    elastic_tensor
    elastic_tensor_original
    homogeneous_poisson	nsites
    poisson_ratio
    universal_anisotropy
    warnings
    **lots for elasticity_third_order so I haven't added these yet

Magnetism
    exchange_symmetry
    is_magnetic	magmoms	num_magnetic_sites
    num_unique_magnetic_sites
    ordering
    total
    total_magnetization
    total_magnetization_normalized_formula_units
    total_magnetization_normalized_vol
    types_of_magnetic_species

Oxides
    type (peroxide/superoxide/etc)

Piezo
    eij_max
    v_max
    piezoelectric_tensor

"""