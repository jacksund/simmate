
# Machine Learning Featurization

## About :star:

This script demonstrates how to load structure data from the database and generate a feature set (fingerprints) suitable for machine learning models. We use Simmate's `PropertyGrabber` to extract physical properties into a pandas DataFrame.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Intermediate**                           |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] Load Materials Project data ([guide](/database/access_thirdparty_data.md))

## The script :rocket:

``` python
from simmate.apps.materials_project.models import MatprojStructure
from simmate.toolkit.featurizers import PropertyGrabber

# 1. Load a set of structures from the database
# For this example, we'll grab the first 100 structures.
db_structures = MatprojStructure.objects.all()[:100]

# 2. Convert database objects to toolkit objects
structures = [s.to_toolkit() for s in db_structures]

# 3. Initialize the featurizer
# We'll grab a simple set of structural properties.
featurizer = PropertyGrabber()
properties_to_grab = [
    "num_sites",
    "volume",
    "density",
]

# 4. Generate the features
# We specify 'pandas' format to get a DataFrame back.
df = featurizer.featurize_many(
    structures,
    properties=properties_to_grab,
    dataframe_format="pandas",
)

# 5. Add the target value (e.g. band gap) from the database
df["band_gap"] = [s.band_gap for s in db_structures]

# 6. Display the results
print(df.head())

# 7. Advanced: Use Matminer
# Simmate's toolkit objects work directly with external libraries like Matminer:
#
# from matminer.featurizers.structure import SiteStatsFingerprint
# matminer_featurizer = SiteStatsFingerprint.from_preset("CoordinationNumber_obw")
# features = matminer_featurizer.featurize_many(structures)
```
