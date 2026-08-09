# Creating Data Apps

A **Data App** is a Simmate App specifically designed to store and distribute a scientific dataset. By packaging your data as an app, you can provide users with a clean API, an ORM for querying, and a way to download the entire dataset in seconds.

----------------------------------------------------------------------

## Why Package Your Data as an App?

When you create a Data App, you're not just sharing a CSV or JSON file. You're giving your data:

1. **A Database Schema**: Your table's columns are clearly defined (energy, spacegroup, etc.).
2. **A Query API**: Users can filter through your data using [the Django ORM](./basic_use.md).
3. **Optimized Storage**: Simmate's `to_archive` method can compress large datasets (e.g., 100,000 structures) into small ZIP files.
4. **Integration**: Your data becomes a first-class citizen in the Simmate ecosystem.

----------------------------------------------------------------------

## Step-by-Step Implementation

### Step 1: Define Your Table
First, [create a Simmate App](../apps/creating_custom_apps.md) and define your table in `models.py`.

``` python
from simmate.database.core import table_column
from simmate.database.mixins import (
    Structure, 
    Thermodynamics,
)

class MyDataset(Structure, Thermodynamics):
    
    # Required for Data Apps
    id = table_column.CharField(max_length=50, primary_key=True)
    source = "My Research Group (2025)"
    source_doi = "https://doi.org/10.1234/..."

    # Your custom columns
    custom_metric = table_column.FloatField(null=True, blank=True)
    
    # Important: Include your columns in 'archive_fields' for sharing
    archive_fields = ["custom_metric"]
    
    # We will set this later in Step 5
    remote_archive_link = None
```

### Step 2: Load Your Data
Write a script to load your raw data (CSV, JSON, etc.) into the Simmate table.

``` python
from my_app.models import MyDataset
from simmate.toolkit import Structure
from rich.progress import track

def load_all_data(data_list):
    for entry in track(data_list):
        # Convert to toolkit structure
        struct = Structure.from_dict(entry["structure_dict"])
        
        # Create and save DB entry
        entry_db = MyDataset.from_toolkit(
            id=entry["id"],
            structure=struct,
            energy=entry["energy"],
            custom_metric=entry["custom_metric"],
        )
        entry_db.save()
```

### Step 3: Create the Archive
Once your data is loaded into your local database, you can create a compressed snapshot (a "Remote Archive") in one line:

``` python
MyDataset.objects.to_archive()
# This creates a file like MyDataset-2025-01-01.zip in your current folder.
```

### Step 4: Host the ZIP File
To make your data accessible to others, you must host the ZIP file at a public URL (e.g., on GitHub, a personal CDN, or a service like Dropbox).

### Step 5: Link the Remote Archive
Update your table definition with the public URL you created in Step 4.

``` python
class MyDataset(Structure, Thermodynamics):
    # ... previous definitions ...
    
    remote_archive_link = "https://example.com/MyDataset-2025-01-01.zip"
```

----------------------------------------------------------------------

## Sharing Your App

Once your app is ready, others can use your data by:

1. Installing your package (e.g., `pip install my-simmate-data-app`).
2. Adding your app to their Simmate config.
3. Running `load_remote_archive`:

``` python
from my_app.models import MyDataset
MyDataset.load_remote_archive()
```

!!! tip
    If you'd like your Data App to be officially included in Simmate's registry, please [open a GitHub issue](https://github.com/jacksund/simmate/issues). We are happy to help you refine and distribute your dataset!

----------------------------------------------------------------------
