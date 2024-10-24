# -*- coding: utf-8 -*-

import warnings

import numpy

from simmate.toolkit.mapping.base import ChemSpaceMapper

# BUG: Importing umap prints various deprec warnings, so we catch
# and silence those here.
with warnings.catch_warnings(record=True):
    import umap


class Umap(ChemSpaceMapper):
    @classmethod
    def map_fingerprints(
        cls,
        fingerprints: list,
        n_outputs: int = 2,
        n_neighbors: int = 10,
        min_dist: float = 0.01,
        low_memory: bool = False,
        **kwargs,
    ):
        mapper = umap.UMAP(
            n_components=n_outputs,  # 2 would mean we want an XY plot
            metric="jaccard",  # aka Tanimoto
            # next two parameters control tightness of the mapping
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            low_memory=low_memory,
            **kwargs,
        )
        fit = mapper.fit_transform(fingerprints)
        return numpy.array([fit[:, n] for n in range(n_outputs)])
