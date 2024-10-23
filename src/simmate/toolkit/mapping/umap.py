# -*- coding: utf-8 -*-

import warnings

from simmate.toolkit.mapping.base import ChemSpaceMapper

# BUG: Importing umap prints various deprec warnings, so we catch
# and silence those here.
with warnings.catch_warnings(record=True):
    import umap


class Umap(ChemSpaceMapper):
    @classmethod
    def map_fingerprints(cls, fingerprints: list, n_outputs: int = 2):
        mapper = umap.UMAP(
            n_components=n_outputs,  # we want an XY plot
            metric="jaccard",  # aka Tanimoto
            # next two parameters control tightness of the mapping
            n_neighbors=25,
            min_dist=0.25,
            low_memory=False,
        )
        fit = mapper.fit_transform(fingerprints)

        if n_outputs == 2:
            fit_x, fit_y = fit[:, 0], fit[:, 1]
            return fit_x, fit_y
        elif n_outputs == 3:
            fit_x, fit_y, fit_z = fit[:, 0], fit[:, 1], fit[:, 2]
            return fit_x, fit_y, fit_z
