# Structure Featurizers

--------------------------------------------------------------------------------

## Overview

Featurizing structures involves generating properties and information about each structure, such as the number of elements, molar mass, and metallic character. These features are crucial for exploring and analyzing data, identifying trends, and training machine learning or artificial intelligence models. The `Featurizer` base class helps optimize this process.

### Fingerprints

Fingerprints are a unique type of featurizer that generate a 1D array of numerical values for each structure. Each value represents a specific feature or property of the structure. Fingerprints are entirely numerical, making them suitable for mathematical applications without requiring additional processing.

--------------------------------------------------------------------------------

## Basic API vs. Featurizer API

The `Featurizer` API and the single-structure API can both be used to calculate a list of properties. The choice between the two depends on your coding style preference and the scale of your project. The `Featurizer` API offers parallelization, which can be beneficial for large-scale projects.

Single Structure ("Basic") API:
``` python
my_final_props = {
    "num_elements": [s.num_elements for s in input_structures],
    "molar_mass": [s.molar_mass for s in input_structures],
    "metallic_character": [s.metallic_character for s in input_structures],
}
```

`Featurizer` API:
``` python
from simmate.toolkit.featurizers import PropertyGrabber

my_final_props = PropertyGrabber.featurize_many(
    structures=input_structures,
    properties=["num_rings", "num_stereocenters", "molecular_weight"],
    parallel=True,  # this is the key reason you'd want to use a Featurizer class!
)
```

!!! tip
    Both APIs yield the same result. The main difference is that the `Featurizer` API can use Dask for parallelization when `parallel=True`. If feature generation takes more than 15 minutes for all structures, we recommend using the `Featurizer` API. This is typically the case when working with datasets of over 1 million structures.

--------------------------------------------------------------------------------

## Usage Guide

All classes that inherit from the `Featurizer` class can be used in the same way. This guide uses the `CrytalnnFingerprint` as an example, but you can substitute it with any supported featurizer.

### Available Featurizers

The `toolkit.featurizers` module contains all available featurizers, including:

- `CrytalnnFingerprint`
- `example....`

### Serial Use

You can featurize molecules one at a time using either the `featurize` or `featurize_many(parallel=False)` methods:

``` python
from simmate.toolkit.featurizers import CrytalnnFingerprint

# OPTION 1
for structure in input_structures:
    fingerprint = CrytalnnFingerprint.featurize(
        structure=structure
    )

# OPTION 2
fingerprints = CrytalnnFingerprint.featurize_many(
    structure=input_structures,
    parallel=False,
)
```

### Parallel Use

Enable parallelization by using the `featurize_many(parallel=True)` method:

``` python
from simmate.toolkit.featurizers import CrytalnnFingerprint

fingerprints = CrytalnnFingerprint.featurize_many(
    structure=input_structures,
    parallel=False,
)
```

--------------------------------------------------------------------------------

## Adding a New Featurizer

To add a new featurizer, you need to:

1. Inherit from the `Featurizer` base class
2. Define a `featurize` method (can be a `@classmethod` or `@staticmethod`) that accepts `structure` as a kwarg.

The `Featurizer` will then handle how `featurize_many` and other features behave.

For example:

``` python
from simmate.toolkit import Structure
from simmate.toolkit.featurizers.base import Featurizer


class Example(Featurizer):
    """
    An example featurizer
    """

    @staticmethod
    def featurize(
        molecule: Structure,
        # feel free to add any extra kwargs you'd like
        example_setting: float = 0.123,
    ):
        # use the molecule to generate your feature(s)
        return calculation_property
```

--------------------------------------------------------------------------------