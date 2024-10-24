# -*- coding: utf-8 -*-

import numpy
from rich.progress import track

from simmate.toolkit.similarity.base import SimilarityEngine

from .base import ClusteringEngine


class Identity(ClusteringEngine):
    """
    Clusters together entries that have a similarity of 1. Note this is most
    often used with the `Identity` SimilarityEngine and it assumes two things:

    1. The fingerprint matrix is binary (1s and 0s only)
    2. Similarities are mutually exclusive. That is, an entry will have a
       similarity of 1 to ONE AND ONLY ONE cluster and 0 for all others
    """

    @classmethod
    def cluster_fingerprints(
        cls,
        fingerprints: list,
        similarity_engine: SimilarityEngine,
        similarity_engine_kwargs: dict = {},
        progress_bar: bool = False,
        flat_output: bool = False,
    ):
        fingerprints = numpy.array(fingerprints)
        n_fingerprints = len(fingerprints)

        clusters = []
        for i in track(range(1, n_fingerprints), disable=not progress_bar):
            found_cluster = False
            for cluster in clusters:
                similarity = similarity_engine.get_similarity(
                    fingerprint1=fingerprints[i],
                    #  only compare to 1st entry bc all should be identical
                    fingerprint2=fingerprints[cluster[0]],
                    **similarity_engine_kwargs,
                )
                if similarity == 1:
                    cluster.append(i)
                    found_cluster = True
                    break  # only one cluster matches so we can stop looking
            if not found_cluster:
                # otherwise we have a new cluster
                clusters.append([i])

        # reformat to tuples to match other clustering methods
        clusters = tuple([tuple(c) for c in clusters])

        # TODO: handle flat_output and other methods. Maybe in base class
        return clusters
