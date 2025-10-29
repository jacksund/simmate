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


def unflatten_cluster_ids(clusters: list[list]) -> list[int]:
    """
    Reverse of flatten_cluster_output

    Takes a flat list of cluster ids like [1, 1, 2, 2, ....] and groups them
    into clusters of the form [[mol1, mol2, ....], [mol3, mol4, ...], ...]
    """
    pass
