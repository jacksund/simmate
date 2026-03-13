# Creating New Tables

In Simmate, you define database tables by inheriting from **Mix-ins**. These mix-ins provide pre-defined columns and methods for common scientific data types, such as crystal structures, energies, and calculation metadata.

----------------------------------------------------------------------

## Mix-in Types

Simmate provides a hierarchy of mix-ins in the `simmate.database.base_data_types` module.

### Low-Level Mix-ins
These are the building blocks for any table:

- `DatabaseTable`: The absolute base. Includes utility methods like `show_columns`.
- `Calculation`: Stores job metadata (run ID, status, timestamps, etc.).
- `Structure`: Stores a periodic crystal structure (lattice, sites, etc.).
- `Thermodynamics`: Stores energy, hull energy, and stability data.
- `Forces`: Stores site forces and lattice stress.
- `BandStructureCalc` / `DensityofStatesCalc`: Stores electronic structure metadata.

### High-Level Mix-ins
These combine multiple low-level mix-ins for common workflow results:

- `StaticEnergy`: `Structure` + `Thermodynamics` + `Forces` + `Calculation`.
- `Relaxation`: Same as `StaticEnergy` but with relationships to the `IonicStep` table.
- `Dynamics`: `Structure` + `Calculation` with relationships to the `DynamicsIonicStep` table.

----------------------------------------------------------------------

## Defining Your Table

To create a new table, you should first [create a Simmate App](../apps/creating_custom_apps.md). Then, add your table to the app's `models.py` file.

``` python
from simmate.database.base_data_types import (
    table_column,
    Structure,
    Thermodynamics,
    Calculation,
)

# Inherit from mix-ins to get their columns automatically
class MyCustomTable(Structure, Thermodynamics, Calculation):
    
    class Meta:
        # 1. Set which Simmate app this belongs to
        # This is only needed if the table isn't in a standard models.py file
        app_label = "my_app"

        # 2. (Optional) Set the actual name of the table in the database
        # We recommend 'app_name__table_name'
        db_table = "my_app__custom_table"
    
    # 3. (Optional) Define a custom ID field
    # By default, Simmate uses an auto-incrementing integer. If your data 
    # has unique string IDs (like "mp-123"), define it as the primary key.
    # Note: 'Calculation' mix-in uses an AutoField by default.
    # id = table_column.CharField(max_length=25, primary_key=True)

    # 4. Add custom columns using 'table_column' (standard Django fields)
    custom_score = table_column.FloatField(null=True, blank=True)
    is_stable = table_column.BooleanField(default=False)

    # 5. (Optional) Define which fields should be included in archives
    # This is useful for sharing your data (see 'Creating Data Apps' guide)
    archive_fields = ["custom_score", "is_stable"]
```

!!! note
    Simmate uses the [Django ORM](https://docs.djangoproject.com/en/5.2/topics/db/models/) under the hood. Any Django field type is supported.

----------------------------------------------------------------------

## Registering and Creating the Table

Once your table is defined in your app, you need to tell Simmate to create it in the database:

1. **Register the app**: Ensure your app is in Simmate's config.
   ```bash
   simmate config add 'my_app.config.MyAppConfig'
   ```

2. **Update the database**: Run the migration command.
   ```bash
   simmate database update
   ```

----------------------------------------------------------------------

## Loading and Saving Data

Use the `from_toolkit` method to create database entries from scientific objects.

``` python
from my_app.models import MyCustomTable
from simmate.toolkit import Structure

# Create a toolkit structure
struct = Structure.from_file("POSCAR")

# Create the database object
entry = MyCustomTable.from_toolkit(
    structure=struct,      # Required by Structure mix-in
    energy=-10.5,          # Required by Thermodynamics mix-in
    custom_score=0.95,     # Your custom column
)

# Save to the database
entry.save()
```

!!! info "How `from_toolkit` Works"
    Simmate uses Python's [method resolution order (MRO)](https://www.python.org/download/releases/2.3/mro/) to automatically discover and combine data from all parent mix-ins. When you call `from_toolkit`, Simmate inspects each mix-in, identifies the arguments it requires (like `structure` or `energy`), and populates the corresponding database columns for you.

----------------------------------------------------------------------
