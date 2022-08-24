
# Creating custom database tables

Inside your project, there are example database tables that show how to build simple ones. It may seems super minimal, but there's really nothing else to do! 

Recall from [the section on inheritance](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md#the-full-tutorial) from tutorial 04. This is why building out new tables is so easy!

Some thing as simple as...

``` python
from simmate.database.base_data_types import (
    table_column,
    Structure,
)


class MyCustomTable1(Structure):
    new_column = table_column.FloatField(null=True, blank=True)
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
- spacegroup (relation to Spacegroup)
- new_column  # <--- note your new column here!
```

You can automatically fill this table using the `from_toolkit` method too:

``` python
from simmate.toolkit import Structure


nacl = Structure.from_file("NaCl.cif")

new_entry = MyCustomTable1.from_toolkit(
    structure=nacl, 
    new_column=3.1415,
)
new_entry.save()
```

There are many more `base_data_types` that you can use, and all types build out features for you automatically. Be sure to read through our guides in the [`simmate.database`](https://jacksund.github.io/simmate/simmate/database.html) module for more info. Advanced database tables may require reading more on the [base data types](https://jacksund.github.io/simmate/simmate/database/base_data_types.html) too.

