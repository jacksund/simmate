# Creating Custom Database Tables

-------------------------------------------------------------------------------

## Constructing Custom Tables

Your project includes example database tables that demonstrate how to construct basic ones. Although it may appear extremely simple, there's no additional work required! 

Remember the lesson on [inheritance](/simmate/getting_started/access_the_database/intro_to_python_inheritance/) from the "access the database" tutorial. This is why creating new tables is straightforward. :fire:

For instance, the following code...

``` python
# This code is for illustrative purposes only. Do not run it.

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Calculation,  # useful for tables used in workflows
)

class MyCustomTable1(Structure, Calculation):
    pass  # no additional requirements unless you want to add custom columns/features

```

... will generate a new database table with the following columns:

```
- created_at
- updated_at
- source
- structure
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

However, we can't import these tables or load data into them just yet. We'll cover that next.

!!! tip
    While we only demonstrate `Structure` and `Calculation` data here, there are many more `base_data_types` you can utilize. All types automatically generate features for you. Make sure to review our guides in the [`simmate.database`](/full_guides/database/overview/) module for more information. Advanced database tables may require further reading on the [base data types](/full_guides/database/custom_tables/).

-------------------------------------------------------------------------------

## Incorporating Tables into Your Database

1. Open the `example_app/models.py` file and review the example tables.

1. Add these tables to your database by updating your database with Simmate:
``` bash
simmate database update
```

2. Verify the output of your `update` command. You should see that your new app and tables have been added.
``` bash
Migrations for 'example_app':
  example_app/migrations/0001_initial.py
    - Create model MyCustomTable2
    - Create model MyCustomTable1
```

3. Ensure you can view the new tables in your database. Remember, we need to connect to our database first. We'll start with `MyCustomTable2`:

``` python
from simmate.database import connect

from example_app.models import MyCustomTable2

MyCustomTable2.objects.count()  # should output 0 as we haven't added data yet
```

!!! danger
    Whenever you modify the `models.py` file, make sure to run `simmate database update` for your changes to take effect in your database.

!!! info
    In Django (which Simmate uses under the hood), a `DatabaseTable` is referred to as a `Model`. Therefore, a model and table can be considered the same. As we're using Django, the file name `models.py` must remain as is. That's where Django searches for your custom database tables.

!!! tip
    `simmate database reset` will also apply your changes to the database. Just ensure you select **no** for the prebuilt database.

-------------------------------------------------------------------------------

## Populating Your New Table with Data

You can automatically populate this table using the `from_toolkit` method:

``` python
from simmate.database import connect
from simmate.toolkit import Structure

from example_app.models import MyCustomTable1

nacl = Structure.from_file("NaCl.cif")

new_entry = MyCustomTable1.from_toolkit(structure=nacl)
new_entry.save()
```

!!! tip
    Manually populating your table with data is often unnecessary. Instead, you can connect your database to a workflow, which will automatically fill it with data. We'll cover this in a later step.

-------------------------------------------------------------------------------

## Searching Your New Data

You can filter results just like any other table. If you need a refresher, refer back to the earlier database tutorial.

``` python
df = MyCustomTable1.objects.filter(nsites__lte=10).to_dataframe()
```

-------------------------------------------------------------------------------