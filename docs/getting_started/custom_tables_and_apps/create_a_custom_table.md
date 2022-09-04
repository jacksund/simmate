# Creating custom database tables

-------------------------------------------------------------------------------

## Build custom tables

Inside your project, there are example database tables that show how to build simple ones. It may seem super minimal, but there's really nothing else to do! 

Recall from [the section on inheritance](https://jacksund.github.io/simmate/getting_started/access_the_database/intro_to_python_inheritance/) from the "access the database" tutorial. This is why building out new tables is so easy. :fire:

Some thing as simple as...

``` python
# Don't run this code. Just read for understanding.

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Calculation,  # useful for tables used in workflows
)

class MyCustomTable1(Structure, Calculation):
    pass  # nothing else is required unless you want to add custom columns/features

```

... will build out a new database table with all the following columns

```
- created_at
- updated_at
- source
- structure_string
- nsites
- nelements
- elements
- chemical_system
- density
- density_atomic
- volume
- volume_molar
- formula_full
- formula_reduced
- formula_anonymous
- spacegroup (points to an entry in the Spacegroup table)
```

However, we won't be able to import these tables or load data just yet. We will cover this next.

!!! tip
    Here we just show `Structure` data, but there are many more `base_data_types` that you can use. All types build out features for you automatically. Be sure to read through our guides in the [`simmate.database`](https://jacksund.github.io/simmate/full_guides/database/overview/) module for more info. Advanced database tables may require reading more on the [base data types](https://jacksund.github.io/simmate/full_guides/database/custom_tables/) too.

-------------------------------------------------------------------------------

## Add tables to your database

1. Once we are happy with our tables in the `models.py` file, we can add them to
our database by Simmate to update our database:
``` bash
simmate database update
```

2. Check the output of your `update` command. You should see that your new app
was detected and that your tables were added.
``` bash
Migrations for 'example_app':
  example_app/migrations/0001_initial.py
    - Create model MyCustomTable2
    - Create model MyCustomTable1
```

3. Make sure you can view the new tables in your database. Just remember
that we need to connect to our database first. Note we are starting with `MyCustomTable2`
here:

``` python
from simmate.database import connect

from example_app.models import MyCustomTable2

MyCustomTable2.objects.count()  # should output 0 bc we haven't added data yet
```

!!! info
    In Django (which Simmate uses under the hood), a `DatabaseTable` is known as
    a `Model`. So a model and table can be viewed as the same thing. Because we
    are using Django, the file name `models.py` must stay this way. That's
    where Django looks for your custom database tables.

!!! tip
    `simmate database reset` will also load your changes to the database. Just
    make sure you say **no** to the prebuilt database.

!!! danger
    Whenever you change the `models.py` file, be sure to either (1) reset your database or (2) run `simmate database update` in order for your changes to be applied to your database.

-------------------------------------------------------------------------------

## Add data to your new table

You can automatically fill this table using the `from_toolkit` method too:

``` python
from simmate.database import connect
from simmate.toolkit import Structure

from example_app.models import MyCustomTable1

nacl = Structure.from_file("NaCl.cif")

new_entry = MyCustomTable1.from_toolkit(structure=nacl)
new_entry.save()
```

!!! tip
    Manually filling your table with data is often not necessary. You can instead
    attach your database to a workflow, which will fill it with data automatically.
    We will learn how to do this in a later step.

-------------------------------------------------------------------------------

## Search your new data

You can filter off results just like you would any other table. Be sure to go
back through the earlier database tutorial if you need a refresher.

``` python
df = MyCustomTable1.objects.filter(nsites__lte=10).to_dataframe()
```

-------------------------------------------------------------------------------
