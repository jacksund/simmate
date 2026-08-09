
# Data Mining & CIF Export

## About :star:

This script demonstrates how to use Simmate's database models and Django's ORM to perform advanced data mining. We query the Materials Project database for stable structures in a specific chemical system (Li-Fe-O) and export the results to CIF files.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] Load the Materials Project data ([guide](/getting_started/database/access_thirdparty_data.md))

## The script :rocket:

``` python
from simmate.database import connect
from simmate.apps.materials_project.models import MatprojStructure

# 1. Query for stable structures in the Li-Fe-O system
# We use 'chemical_system' which stores elements in alphabetical order (Fe-Li-O).
# We filter for 'is_stable=True' to get structures on the convex hull.
structures = MatprojStructure.objects.filter(
    chemical_system="Fe-Li-O",
    is_stable=True,
).all()

print(f"Found {len(structures)} stable structures in the Li-Fe-O system.")

# 2. Iterate through results and export to CIF
for structure_db in structures:
    
    # Convert the database object to a toolkit object
    structure = structure_db.to_toolkit()
    
    # Export to CIF format
    filename = f"{structure_db.id}_{structure.composition.reduced_formula}.cif"
    structure.to(filename=filename, fmt="cif")
    
    print(f"Exported {filename}")

# 3. Advanced: Filter by property ranges
# Find all Li-Fe-O structures (stable or not) with a band gap > 2.0 eV
insulators = MatprojStructure.objects.filter(
    chemical_system="Fe-Li-O",
    band_gap__gt=2.0,
).all()

print(f"Found {len(insulators)} insulating structures in Li-Fe-O.")
```
