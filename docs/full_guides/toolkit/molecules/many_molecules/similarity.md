# Molecular Similarity & Distance

--------------------------------------------------------------------------------

## Overview

"Similarity" and "distance" are **mathematical measures** used to quantify the likeness or difference between molecules. 

To compare molecules, we first need a "description" of each molecule, which is obtained from features or fingerprints (refer to the `Featurizers` section). We then apply a mathematical operator to determine the "distance" between these fingerprints.

The process of comparing molecules typically involves:

1. Generating a fingerprint for each molecule **OR** starting with a pre-existing list of fingerprints
2. Applying a distance formula to quantify the proximity of two fingerprints

The `SimilarityEngine` class manages these steps.

!!! example
    Suppose we want to compare two molecules based on three features:

    - Fraction of sp3 carbons
    - Number of hydrogen donors
    - Number of hydrogen acceptors

    We measure these values for each molecule, resulting in a "fingerprint" of `[x,y,z]`:

    - Molecule 1: `[0.345, 5, 6]`
    - Molecule 2: `[0.543, 2, 1]`

    To determine the similarity, we can "plot" these fingerprints in 3D space and calculate the "distance" between these points. If we're interested in similarity rather than distance, we can consider them as inverses of each other:

    - `distance^2 = (x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2`
    - `similarity = 1 / distance`

    Using these rules, the "similarity" of these two molecules is scored as `0.17`.

    In this example, we used a basic fingerprint (3 features) and the `Euclidean` formula for distance. However, there are numerous ways to generate fingerprints (some with >1000 features!) and calculate distance. The same process and concepts apply to each.

--------------------------------------------------------------------------------

## Basic Use

We'll use `Tanimoto` as an example here, but all methods behave similarly.

### 1. Select a fingerprint method

Choose any fingerprint method from the `simmate.toolkit.featurizers` module. Refer to the Featurizers section for all options. For this example, we'll use `MorganFingerprint`:

``` python
from simmate.toolkit.featurizers import MorganFingerprint
```


### 2. Select a similarity metric

Choose an appropriate metric for similarity based on the selected fingerprint. The following types of similarity/distance measurements are supported:

| CLASS       |
| ----------- |
| `Cosine`    |
| `Dice`      |
| `Euclidean` |
| `Tanimoto`  |

``` python
from simmate.toolkit.similarity import Tanimoto
```


!!! warning
    For many fingerprints, there is a "logical & correct" choice for the metric to use. If you're unsure, don't guess! Seek help & advice :smile:

    For instance, the `MorganFingerprint` that we selected in step 1 is most effective when used with `Tanimoto`.

### 2. Select a similarity method

All `SimilarityEngine` subclasses support the following methods:

| CLASS                                                                                  |
| -------------------------------------------------------------------------------------- |
| `get_similarity(fingerprint1, fingerprint2)`                                           |
| `get_similarity_series(fingerprint1, [fingerprint2, fingerprint3, fingerprint4, ...])` |
| `get_similarity_matrix([fingerprint1, fingerprint2, fingerprint3, ...])`               |
| `get_distance(fingerprint1, fingerprint2)`                                             |
| `get_distance_series(fingerprint1, [fingerprint2, fingerprint3, fingerprint4, ...])`   |
| `get_distance_matrix([fingerprint1, fingerprint2, fingerprint3, ...])`                 |

Suppose we have a single molecule that we want to compare to a set of 1,000 molecules. For this, we'll use `get_similarity_series`:

``` python
Tanimoto.get_similarity_series
```

### 3. Construct the final script

Now, let's combine everything for our final script.

``` python
from simmate.toolkit import Molecule
from simmate.toolkit.featurizers import MorganFingerprint
from simmate.toolkit.similarity import Tanimoto

# Load query molecule
query_molecule = Molecule.from_smiles(".....")

# Load other molecules
smiles_strs = [......] 
molecules = [Molecule.from_smiles(s) for s in smiles_strs]

# Generate fingerprints
query_fingerprint = MorganFingerprint.featurize(query_molecule)
fingerprints = MorganFingerprint.featurize_many(molecules)

# Generate the similarity scores
similarities = Tanimoto.get_similarity_series(
    query_fingerprint,
    fingerprints,
)
```

--------------------------------------------------------------------------------