# -*- coding: utf-8 -*-

from sklearn.manifold import TSNE

from simmate.toolkit.mapping.base import ChemSpaceMapper


class Tsne(ChemSpaceMapper):
    @classmethod
    def map_fingerprints(cls, fingerprints: list, n_outputs: int = 2):
        # 2 components --> gives a 2d (XY) plot
        mapper = TSNE(n_components=n_outputs)
        fit = mapper.fit_transform(fingerprints)

        if n_outputs == 2:
            fit_x, fit_y = fit[:, 0], fit[:, 1]
            return fit_x, fit_y
        elif n_outputs == 3:
            fit_x, fit_y, fit_z = fit[:, 0], fit[:, 1], fit[:, 2]
            return fit_x, fit_y, fit_z
