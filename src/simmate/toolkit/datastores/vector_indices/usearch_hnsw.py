# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import zstandard as zstd
from usearch.index import (
    CompiledMetric,
    Index,
    Indexes,
    MetricKind,
    MetricSignature,
    ScalarKind,
)

from simmate.utils import chunk_list, dispatch

from .base import VectorIndex


class UsearchHnswIndex(VectorIndex):
    """
    USearch HNSW graph over the packed bits with an exact Tanimoto metric.
    Exact distances, but the graph itself is large on disk.
    """

    index_suffix: str = "usearch"

    def build(self, datastore_cls, parallel_job: bool = False) -> None:
        chunk_keys = list(range(datastore_cls.num_chunks))
        batches = [list(b) for b in chunk_list(chunk_keys, self.batch_size)]

        built = self._built_shard_names(datastore_cls)
        batches_to_process = [
            b
            for b in batches
            if self._shard_name(b) not in built
            and f"{self._shard_name(b)}.zst" not in built
        ]

        logging.info(
            f"{len(batches) - len(batches_to_process)} batches already done, "
            f"{len(batches_to_process)} to process"
        )

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

        cfg = datastore_cls._VECTOR_CONFIGS[self.column_name]
        index = Index(
            ndim=cfg["ndim"],
            dtype=ScalarKind.B1,
            metric=CompiledMetric(
                pointer=cfg["metric_fn"].address,
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

            if self._use_zstd():
                compressed = zstd.ZstdCompressor().compress(
                    uncompressed_path.read_bytes()
                )
                index_path.write_bytes(compressed)

            logging.info(f"  Saved progress | Vectors: {len(index):,}")

        if self._use_zstd():
            uncompressed_path.unlink(missing_ok=True)

    def load(self, datastore_cls) -> None:
        if self._cached_payload is not None and self._cached_mode == self.load_mode:
            return

        mode = self.load_mode
        if mode not in ["memory", "view", "scan", "scan-zstd"]:
            raise ValueError(
                f"Unknown load_mode: {mode!r}. "
                "Use 'memory', 'view', 'scan', or 'scan-zstd'."
            )

        index_files = self._index_files(datastore_cls)
        if not index_files:
            raise FileNotFoundError(
                f"No {self.column_name} usearch index files found in "
                f"{self.vectors_directory(datastore_cls)}. "
                "Run build() first."
            )

        n_files = f"{len(index_files)} {self.column_name} usearch index file(s)"
        if mode == "memory":
            logging.info(f"Loading {n_files} into RAM...")
            payload = [self._read_index(p, into_memory=True) for p in index_files]
            n_vectors = sum(len(i) for i in payload)
            logging.info(f"Loaded {n_vectors:,} vectors.")
        elif mode == "view":
            logging.info(f"Opening {n_files} as memory-mapped views...")
            payload = Indexes(paths=[str(p) for p in index_files], view=True)
        else:
            logging.info(f"Registering {n_files} for scan-mode search.")
            payload = index_files

        self._cached_mode = mode
        self._cached_payload = payload

    def _read_index(self, path: Path, into_memory: bool = False):
        is_zstd = path.suffix == ".zst"
        raw = zstd.ZstdDecompressor().decompress(path.read_bytes()) if is_zstd else None

        if is_zstd:
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
            return self._hits_dataframe(keys, distances, count)

        all_keys, all_distances = [], []
        for index in self._iter_indexes():
            matches = index.search(vec, count)
            all_keys.extend(matches.keys.tolist())
            all_distances.extend(matches.distances.tolist())
        return self._hits_dataframe(all_keys, all_distances, count)
