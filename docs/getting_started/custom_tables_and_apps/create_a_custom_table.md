# Creating Custom Database Tables

-------------------------------------------------------------------------------

## Building Custom Tables

1. Review the tutorial on [python inheritance](../../database/intro_to_python_inheritance/) (from the `How tables are built` tutorial in the `Database` section). This topic is important to understanding when building new tables. 

2. In your new app, open the file `example_app/models.py` and you will see two example tables defined for you. This is all you need to build tables! Note, how we also use `Structure` and `Calculation` to add a bunch of columns to in the 2nd table:
``` python
class MyCustomTable1(DatabaseTable):
    custom_column_01 = table_column.IntegerField()
    custom_column_02 = table_column.FloatField()

class MyCustomTable2(Structure, Calculation):
    input_01 = table_column.FloatField()
    input_02 = table_column.BooleanField()
    output_01 = table_column.FloatField(null=True, blank=True)
    output_02 = table_column.BooleanField(null=True, blank=True)
```

    !!! tip
        We only demonstrate `Structure` and `Calculation` in the examples shown, but there are many more `base_data_types` you can utilize. Make sure to review our guides in the [`simmate.database`](/full_guides/database/overview/) module for more information.
    
    !!! info
        In Django (which Simmate uses under the hood), a `DatabaseTable` is referred to as a `Model`. Therefore, a model and table can be considered the same. As we're using Django, the file name `models.py` must remain as-is. That's where Django searches for your custom database tables.

3. These examples will build tables with the following columns:
```
# TABLE 1

# TABLE 2

```

4. Note... These tables are not actually in your database yet. You can check your tables in DBeaver to confirm this. Next, we will actually "apply" them to our database.

-------------------------------------------------------------------------------

## Applying Changes to the Database

1. Open the `example_app/models.py` file and review the example tables.

2. Ensure the Simmate configuration includes your new app:
``` bash
simmate config show --user-only
```

3. Add these tables to the database by updating it:
``` bash
simmate database update
```

    !!! note
        The `update` command attempts to add any changes to your current database. If you wish to start from a clean and empty database, you can use `reset` instead.

4. Verify the output of your `update` command. You should see that your new app and tables have been added.
``` bash
Migrations for 'example_app':
  example_app/migrations/0001_initial.py
    - Create model MyCustomTable1
    - Create model MyCustomTable2
```

    !!! danger
        All changes are tracked as "migrations" and stored in an extra folder within your app. Typically, you can just continue to let these files build because migrations are designed to be committed to, and distributed as part of, your codebase. Make sure to read & understand Django's [official guides](https://docs.djangoproject.com/en/5.0/topics/migrations/) on how to interact with these files.

5. Check DBeaver and you should see new tables such as `example_app_mycustomtable1` and `example_app_mycustomtable2`

6. In a separate python script, let's ensure we can view the new tables in your database:
``` python
from simmate.database import connect

from example_app.models import MyCustomTable1, MyCustomTable2

# both tables should output 0 because we haven't added data yet
n1 = MyCustomTable1.objects.count()  
n2 = MyCustomTable2.objects.count()  
```

7. You now have your tables in the database! 

    !!! note
        If you ever change your tables (such as adding or removing a column), you will need to re-update your database. Therefore, whenever you modify the `models.py` file, make sure to run `simmate database update` for your changes to take effect in your database.

-------------------------------------------------------------------------------

## Adding Data to Your Tables

### Basic Population

For basic tables, you can set each column manually:

``` python
from simmate.database import connect
from example_app.models import MyCustomTable1

new_entry = MyCustomTable1(
    custom_column_01=123,
    custom_column_02=3.14,
)
new_entry.save()
```

Once saved, try viewing your new row in DBeaver!

### Advanced population

For more complex tables that include Simmate data types, we automatically populate data using the `from_toolkit` method:

``` python
from simmate.database import connect
from simmate.toolkit import Structure

from example_app.models import MyCustomTable2

nacl = Structure.from_file("NaCl.cif")

new_entry = MyCustomTable2.from_toolkit(structure=nacl)
new_entry.save()
```

Once saved, try viewing your new row in DBeaver. You will see many columns were filled out automatically. Some columns are still empty though (such as those from a `Calculation`). We will learn how to populate these tables in the next tutorial on `Adding app workflows`

!!! tip
    Manually populating your table with data is often unnecessary. Instead, you can connect your database to a workflow, which will automatically fill it with data. We'll cover this in a later step.

-------------------------------------------------------------------------------

## Searching Your New Data

You can filter results just like any other table. If you need a refresher, refer back to the earlier database tutorial or refer to the Full Guides for more info:

``` python
df = MyCustomTable2.objects.filter(nsites__lte=10).to_dataframe()
```

-------------------------------------------------------------------------------