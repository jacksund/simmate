# ChemSpace Mapping

--------------------------------------------------------------------------------

## Overview

ChemSpace mapping refers to the process of plotting molecules in a 2D or 3D coordinate system, enabling the visualization of molecule similarities. Each data point in the plot represents a unique molecule, with closer points indicating more similar molecules.

![ChemSpace Mapping Example](https://s3.amazonaws.com/reverie-ghost/2021/03/tsne_original--1.png){ width=300px }

The process typically involves three steps:

1. Generating a fingerprint for each molecule or starting with a list of fingerprints.
2. Converting the multi-value fingerprints into condensed fingerprints with 2-3 coordinates.
3. Plotting the 2D or 3D coordinates to visualize molecule similarities.

The `ChemSpaceMapper` class manages these steps.

--------------------------------------------------------------------------------

## Basic Use (`from_preset`)

In most cases, you can use the recommended settings for clustering, which are stored in the `ChemSpaceMapper.from_preset` method. Presets are named using the format `[mapping method]-[fingerprint method]`. Currently, we provide the `umap-morgan` preset.

Here's an example of chemspace mapping using default settings:

``` python
from simmate.toolkit.mapping import ChemSpaceMapper

x,y = ChemSpaceMapper.from_preset(
    molecules=[...],  # This should be a list of Molecule objects
    preset="umap-morgan",
    n_outputs=2,  # For a 2D (XY) plot
)
```

!!! tip
    If you want to customize parameters for mapping/fingerprints, consider using the advanced API below.

--------------------------------------------------------------------------------

## Advanced Use

For complete control over your chemspace mapping, you can manually select your methods and parameters. 

### 1. Choose Fingerprint Method

Select a fingerprint method from the `simmate.toolkit.featurizers` module. You can also select any kwargs that the featurizer's `featurize_many` method accepts. Refer to the [Featurizers](#) section for all available featurizers and their kwarg options.

Example:
``` python
from simmate.toolkit.featurizers import MorganFingerprint

featurizer_kwargs = dict(
    radius=4,
    nbits=2048,
    parallel=True,
)
```

### 2. Choose Mapping Method

Select a mapping method from the `simmate.toolkit.clustering` module. You can also select any kwargs that the `map_fingerprints` method accepts. We currently support `Pca`, `Tsne`, and `Umap` methods.

Example:
``` python
from simmate.toolkit.mapping import Umap

mapping_kwargs = dict(
    metric="jaccard",  # aka Tanimoto
    n_neighbors=25,
    min_dist=0.25,
    low_memory=False,
)
```

!!! note
    All mapping methods have a `map_molecules` and a `map_fingerprints` method. These methods will be called in the final scripts.

### 3. Final Script

Once you've selected your methods and parameters, you can put them together:

``` python
from simmate.toolkit.clustering import Butina
from simmate.toolkit.mapping import Umap

x, y = Umap.map_molecules(
    molecules=[...],  # This should be a list of Molecule objects
    featurizer=MorganFingerprint,
    featurizer_kwargs = dict(
        radius=4,
        nbits=2048,
        parallel=True,
    ),
    metric="jaccard",
    n_neighbors=25,
    min_dist=0.25,
    low_memory=False,
)
```

### EXTRA: Starting from Fingerprints

If you already have fingerprints and want to use those instead of `Molecule` objects, you can skip the first step and replace `map_molecules` with the `map_fingerprints` method:

``` python
from simmate.toolkit.clustering import Butina
from simmate.toolkit.mapping import Umap

clusters = Umap.map_molecules(
    fingerprints=[...],  # This should be a list of fingerprints (1D array of floats)
    metric="jaccard",
    n_neighbors=25,
    min_dist=0.25,
    low_memory=False,
)
```

--------------------------------------------------------------------------------

## Adding a New Mapping Method

To add a new mapping method, you need to:

1. Inherit from the `ChemSpaceMapper` base class.
2. Define a `map_fingerprints` method (can be a `@classmethod` or `@staticmethod`) that accepts `fingerprints` and `n_outputs` as kwargs.

The `ChemSpaceMapper` will then manage how `map_molecules`, `map_fingerprints`, and other features behave.

For example:

``` python
from simmate.toolkit.mapping.base import ChemSpaceMapper


class Example(ChemSpaceMapper):
    """
    An example mapping algo
    """

    @classmethod
    def map_fingerprints(
        cls, 
        fingerprints: list, 
        n_outputs: int = 2,
        example_setting: float = 0.123,
    ):
        # add your mapping algo
        if n_outputs == 2:
            # ....
            return fit_x, fit_y
        elif n_outputs == 3:
            # ....
            return fit_x, fit_y, fit_z
```

--------------------------------------------------------------------------------