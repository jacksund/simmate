# Molecule Clustering

--------------------------------------------------------------------------------

## Overview

Molecule clustering is a three-step process:

1. Generate a fingerprint for each molecule **OR** start with a pre-existing list of fingerprints
2. Create a similarity matrix using these fingerprints
3. Group molecules based on the similarity matrix

The `ClusteringEngine` class manages these steps.

--------------------------------------------------------------------------------

## Basic Use (`from_preset`)

For most applications, you can use the "recommended" settings for clustering. These are stored in the `ClusteringEngine.from_preset` method.

Presets are named using the format `[clustering method]-[similarity method]-[fingerprint method]`. Currently, we offer the following preset:

- `butina-tanimoto-morgan`

Here's an example of clustering using default settings:

``` python
from simmate.toolkit.clustering import ClusteringEngine

clusters = ClusteringEngine.from_preset(
    molecules=[...],  // should be a list of Molecule objects
    preset="butina-tanimoto-morgan",
)
```

!!! tip
    If you wish to customize parameters for clustering/similarity/fingerprint, consider using the "advanced" API below.

--------------------------------------------------------------------------------

## Advanced Use

For full control over molecule clustering, you need to select your methods & parameters. This process uses the same base classes as the preset `butina-tanimoto-morgan`.

### 1. Choose fingerprint method

Select any fingerprint method from the `simmate.toolkit.featurizers` module. You can also select *any* kwargs that the featurizer's `featurize_many` method accepts. Refer to the [Featurizers](#) section for all available featurizers and their kwarg options.

Example:
``` python
from simmate.toolkit.featurizers import MorganFingerprint

featurizer_kwargs = dict(
    radius=4,
    nbits=2048,
    parallel=True,
)
```

### 2. Choose similarity metric

Select any similarity metric from the `simmate.toolkit.similarity` module. You can also select *any* kwargs that the similarity's `get_similarity_matrix` method accepts. Refer to the [Fingerprint Similarities/Distances](#) section for all available similarity metrics and their kwarg options.

Example:
``` python
from simmate.toolkit.similarity import Tanimoto

similarity_engine_kwargs = dict(
    parallel=True,
)
```

### 3. Choose clustering method

Select any clustering method from the `simmate.toolkit.clustering` module. You can also select *any* kwargs that `cluster_fingerprints` method accepts. Currently, we support the following clustering method:

- `Butina`

Example:
``` python
from simmate.toolkit.featurizers import Butina

clustering_kwargs = dict(
    similarity_cutoff=0.50,
    reorder_after_new_cluster=True,
    progress_bar=True,
    flat_output=True,
)
```

!!! note
    All clustering methods have a `cluster_molecules` and a `cluster_fingerprints` method. These methods are what we will be calling in our final scripts (below).

### 4. Final script

Now that we have everything selected, let's put it together:

``` python
from simmate.toolkit.clustering import Butina
from simmate.toolkit.featurizers import MorganFingerprint
from simmate.toolkit.similarity import Tanimoto

clusters = Butina.cluster_molecules(
    molecules=[...],  // should be a list of Molecule objects
    featurizer=MorganFingerprint,
    featurizer_kwargs = dict(
        radius=4,
        nbits=2048,
        parallel=True,
    ),
    similarity_engine=Tanimoto,
    similarity_engine_kwargs = dict(
        parallel=True,
    ),
    similarity_cutoff=0.50,
    reorder_after_new_cluster=True,
    progress_bar=True,
    flat_output=True,
)
```

### EXTRA: Starting from fingerprints

If you already have fingerprints and want to use those instead of `Molecule` objects, you can skip STEP 1 and replace `cluster_molecules` with the `cluster_fingerprints` method:

``` python
from simmate.toolkit.clustering import Butina
from simmate.toolkit.featurizers import MorganFingerprint
from simmate.toolkit.similarity import Tanimoto

clusters = Butina.cluster_molecules(
    fingerprints=[...],  // should be a list of fingerprints (1D array of floats)
    similarity_engine=Tanimoto,
    similarity_engine_kwargs = dict(
        parallel=True,
    ),
    similarity_cutoff=0.50,
    reorder_after_new_cluster=True,
    progress_bar=True,
    flat_output=True,
)
```

--------------------------------------------------------------------------------

## Adding a New Clustering Method

### Standard Method

All clustering methods must:

1. Inherit from the `ClusteringEngine` base class
2. Define a `cluster_similarity_matrix` method (can be a `@classmethod` or `@staticmethod`) that accepts the `similarity_matrix` as a kwarg.

The `ClusteringEngine` will then manage how `cluster_molecules`, `cluster_fingerprints`, and other features behave.

Example:

``` python
from simmate.toolkit.clustering.base import ClusteringEngine
from simmate.toolkit.similarity.base import SimilarityEngine


class Example(ClusteringEngine):
    """
    An example clustering algo
    """

    @classmethod
    def cluster_similarity_matrix(
        cls,
        similarity_matrix: list[list[float]],
        example_setting: float = 0.123,
    ):
        // add your clustering algo
        return clusters
```

### Memory-Optimized Method

When working with >200k molecules, creating a similarity matrix becomes a memory issue because a >200k x >200k matrix will crash on something like a laptop with 16GB of RAM. In such cases, a method like `cluster_similarity_matrix` becomes problematic and sometimes unusable.

To address this, *some* clustering algorithms can be rearranged to "lazily" generate similarity series. For these clustering methods, you should define a `cluster_fingerprints` method instead of a `cluster_similarity_matrix` method.

So here we need to:

1. Inherit from the `ClusteringEngine` base class
2. Define a `cluster_fingerprints` method (can be a `@classmethod` or `@staticmethod`) that accepts the following kwargs: `fingerprints`, `similarity_engine`, and `similarity_engine_kwargs`.

The `ClusteringEngine` will then manage how `cluster_molecules` and other features behave.

Example:

``` python
from simmate.toolkit.clustering.base import ClusteringEngine
from simmate.toolkit.similarity.base import SimilarityEngine


class Example(ClusteringEngine):
    """
    An example clustering algo
    """

    @classmethod
    def cluster_fingerprints(
        cls,
        fingerprints: list,
        similarity_engine: SimilarityEngine,
        similarity_engine_kwargs: dict = {},
        example_setting: float = 0.123,
    ):
        // add your clustering algo
        return clusters
```

!!! tip
    For an example of this approach, see the `Butina` clustering method's source code [here](#UPDATE TO GITHUB LINK)

--------------------------------------------------------------------------------