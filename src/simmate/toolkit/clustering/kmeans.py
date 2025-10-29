# -*- coding: utf-8 -*-

import numpy
from sklearn.cluster import KMeans, kmeans_plusplus

from .base import ClusteringEngine
from .utilities import unflatten_cluster_ids


class Kmeans(ClusteringEngine):
    @classmethod
    def cluster_fingerprints(
        cls,
        fingerprints: list,
        n_clusters: int,
        random_state: int = 0,
        return_centers: bool = False,
        flat_output: bool = False,
    ):
        # sklearn only supports the built-in Euclidean distance, so I disable
        # accepting any sim engine kwargs
        #
        # from ..similarity import Euclidean, SimilarityEngine
        # similarity_engine: SimilarityEngine = Euclidean,
        # similarity_engine_kwargs: dict = {},

        fingerprints = numpy.array(fingerprints)

        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
        cluster_ids = kmeans.fit_predict(fingerprints)

        result = cluster_ids if flat_output else unflatten_cluster_ids(cluster_ids)

        if return_centers:
            centers_init, centers_indicies = kmeans_plusplus(
                fingerprints,
                n_clusters=n_clusters,
                random_state=random_state,
            )
            result = (centers_indicies, result)

        return result
