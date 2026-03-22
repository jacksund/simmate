# -*- coding: utf-8 -*-


def flatten_clusters(clusters: list[list]) -> list[int]:
    """
    Takes a list of clusters of the form [[mol1, mol2, ....], [mol3, mol4, ...], ...]
    and flattens to a list of cluster ids like [1, 1, 2, 2, ....]
    """
    n_entries = sum([len(c) for c in clusters])
    column_ids = []
    for entry_index in range(n_entries):
        for cluster_index, cluster in enumerate(clusters):
            if entry_index in cluster:
                column_ids.append(cluster_index)
                break
    return column_ids


def unflatten_cluster_ids(cluster_ids: list[int]) -> list[list]:
    """
    Reverse of flatten_cluster_output

    Takes a flat list of cluster ids like [1, 1, 2, 2, ....] and groups them
    into clusters of the form [[mol1, mol2, ....], [mol3, mol4, ...], ...]
    """
    n_clusters = max(cluster_ids) + 1  # bc counting starts at 0
    clusters = [[] for _ in range(n_clusters)]
    for entry_index, cluster_id in enumerate(cluster_ids):
        clusters[cluster_id].append(entry_index)
    return clusters
