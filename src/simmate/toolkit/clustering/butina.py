# -*- coding: utf-8 -*-

import numpy
from rich.progress import track

from .base import ClusteringEngine, SimilarityEngine


class Butina(ClusteringEngine):
    @classmethod
    def cluster_fingerprints(
        cls,
        fingerprints: list,
        similarity_engine: SimilarityEngine,
        similarity_engine_kwargs: dict = {},
        similarity_cutoff: float = 0.50,
        reorder_after_new_cluster: bool = True,
        progress_bar: bool = False,
        flat_output: bool = False,
    ):
        fingerprints = numpy.array(fingerprints)
        n_fingerprints = len(fingerprints)
        neighbor_lists = [[] for _ in range(n_fingerprints)]

        for i in track(range(1, n_fingerprints), disable=not progress_bar):
            distances = similarity_engine.get_similarity_series(
                fingerprint1=fingerprints[i],
                fingerprints=fingerprints[:i],
                **similarity_engine_kwargs,
            )
            for j in range(i):
                if distances[j] >= similarity_cutoff:
                    neighbor_lists[i].append(j)
                    neighbor_lists[j].append(i)

        # sort by the number of neighbors
        tLists = [(len(y), x) for x, y in enumerate(neighbor_lists)]
        tLists.sort(reverse=True)

        res = []
        seen = [0] * n_fingerprints
        while tLists:
            _, idx = tLists.pop(0)
            if seen[idx]:
                continue
            tRes = [idx]
            for nbr in neighbor_lists[idx]:
                if not seen[nbr]:
                    tRes.append(nbr)
                    seen[nbr] = 1
            # update the number of neighbors:
            # remove all members of the new cluster from the list of
            # neighbors and reorder the tLists
            if reorder_after_new_cluster:
                # get the list of affected molecules, i.e. all molecules
                # which have at least one of the members of the new cluster
                # as a neighbor
                nbrNbr = [neighbor_lists[t] for t in tRes]
                nbrNbr = frozenset().union(*nbrNbr)
                # loop over all remaining molecules in tLists but only
                # consider unassigned and affected compounds
                for x, y in enumerate(tLists):
                    y1 = y[1]
                    if seen[y1] or (y1 not in nbrNbr):
                        continue
                    # update the number of neighbors
                    neighbor_lists[y1] = set(neighbor_lists[y1]).difference(tRes)
                    tLists[x] = (len(neighbor_lists[y1]), y1)
                # now reorder the list
                tLists.sort(reverse=True)
            res.append(tuple(tRes))

        clusters = tuple(res)

        if flat_output:
            column_ids = []
            for mol_index in range(len(fingerprints)):
                for cluster_index, cluster in enumerate(clusters):
                    if mol_index in cluster:
                        column_ids.append(cluster_index)
                        break
            return column_ids
        else:
            return clusters
