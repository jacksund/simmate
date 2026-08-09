# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from usearch.index import (
    CompiledMetric,
    Index,
    Indexes,
    MetricKind,
    MetricSignature,
    ScalarKind,
)

from simmate.utils import dispatch

from .base import VectorIndex, get_hits_dataframe


class UsearchHnswIndex(VectorIndex):
    """
    USearch HNSW graph over the packed bits with an exact Tanimoto metric.
    Exact distances, but the graph itself is large on disk.
    """

    index_suffix: str = "usearch"
    valid_load_modes: list[str] = ["memory", "view", "scan", "scan-zstd"]

    def build(self, datastore_cls, parallel_job: bool = False) -> None:
        batches_to_process = self._get_pending_batches(datastore_cls)

        dispatch(
            batches_to_process,
            self._build_batch,
            parallel="job" if parallel_job else "single",
            datastore_cls=datastore_cls,
        )
        logging.info("usearch index build complete!")

    def _build_batch(self, batch: list[int], datastore_cls):
        uncompressed_path, index_path = self._shard_paths(datastore_cls, batch)
        logging.info(
            f"Building {self.column_name} batch {batch[0]}-{batch[-1]} → {index_path}"
        )

        index = Index(
            ndim=self.ndim,
            dtype=ScalarKind.B1,
            metric=CompiledMetric(
                pointer=self.metric_fn.address,
                kind=MetricKind.Tanimoto,
                signature=MetricSignature.ArrayArray,
            ),
            path=str(uncompressed_path),
        )

        for chunk_key in batch:
            logging.info(f"  {self.column_name} chunk_key={chunk_key}")
            df = self._chunk_vectors(datastore_cls, chunk_key).collect()
            if len(df) == 0:
                continue

            keys = df["datastore_id"].to_numpy()
            if len(index) > 0 and keys[0] in index:
                logging.info(f"  Skipping chunk_key={chunk_key} - already indexed.")
                continue

            index.add(keys, self._packed_vectors(datastore_cls, df))
            index.save(str(uncompressed_path))

            if self.use_zstd:
                self._write_bytes(
                    uncompressed_path.read_bytes(), index_path, use_zstd=True
                )

            logging.info(f"  Saved progress | Vectors: {len(index):,}")

        if self.use_zstd:
            uncompressed_path.unlink(missing_ok=True)

    def _load_payload(self, index_files: list[Path], n_files_str: str):
        if self.load_mode == "memory":
            logging.info(f"Loading {n_files_str} into RAM...")
            payload = [self._read_index(p, into_memory=True) for p in index_files]
            n_vectors = sum(len(i) for i in payload)
            logging.info(f"Loaded {n_vectors:,} vectors.")
        elif self.load_mode == "view":
            logging.info(f"Opening {n_files_str} as memory-mapped views...")
            payload = Indexes(paths=[str(p) for p in index_files], view=True)
        else:
            logging.info(f"Registering {n_files_str} for scan-mode search.")
            payload = index_files
        return payload

    def _read_index(self, path: Path, into_memory: bool = False):
        is_zstd = path.suffix == ".zst"

        if is_zstd:
            raw = self._read_bytes(path)
            return Index.restore(raw)
        if into_memory:
            return Index.restore(str(path))
        return Indexes(paths=[str(path)], view=True)

    def _iter_indexes(self):
        if self._cached_mode == "memory":
            return self._cached_payload
        return (self._read_index(path) for path in self._cached_payload)

    def search(self, datastore_cls, vec, count: int = 50):
        self.load(datastore_cls)

        if self._cached_mode == "view":
            matches = self._cached_payload.search(vec, count)
            keys, distances = matches.keys.tolist(), matches.distances.tolist()
            return get_hits_dataframe(keys, distances, count)

        all_keys, all_distances = [], []
        for index in self._iter_indexes():
            matches = index.search(vec, count)
            all_keys.extend(matches.keys.tolist())
            all_distances.extend(matches.distances.tolist())
        return get_hits_dataframe(all_keys, all_distances, count)
