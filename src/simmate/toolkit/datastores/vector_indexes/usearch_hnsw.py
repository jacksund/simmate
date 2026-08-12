# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import polars
from usearch.index import (
    CompiledMetric,
    Index,
    Indexes,
    MetricKind,
    MetricSignature,
    ScalarKind,
)

from .base import VectorIndex


class UsearchHnswIndex(VectorIndex):
    """
    USearch HNSW graph over the packed bits with an exact Tanimoto metric.
    Exact distances, but the graph itself is large on disk.
    """

    index_suffix: str = "usearch"
    requires_metric_fn: bool = True

    def _build_batch(self, batch: list[int]) -> None:
        # usearch builds into a plain file, which is then renamed (or
        # compressed) into place once the whole batch is done
        working_path = self._shard_path(batch, ".partial")
        logging.info(
            f"Building {self.column_name} batch {batch[0]}-{batch[-1]} → "
            f"{self._final_shard_path(batch)}"
        )

        # picks up an existing .partial, so an interrupted batch resumes here
        index = Index(
            ndim=self.ndim,
            dtype=ScalarKind.B1,
            metric=CompiledMetric(
                pointer=self.metric_fn.address,
                kind=MetricKind.Tanimoto,
                signature=MetricSignature.ArrayArray,
            ),
            path=str(working_path),
        )

        for chunk_key in batch:
            logging.info(f"  {self.column_name} chunk_key={chunk_key}")
            df = self._chunk_vectors(chunk_key).collect()
            if df.is_empty():
                continue

            keys = df["datastore_id"].to_numpy()
            if len(index) > 0 and keys[0] in index:
                logging.info(f"  Skipping chunk_key={chunk_key} - already indexed.")
                continue

            index.add(keys, self._packed_vectors(df))

            # saved after every chunk so an interrupted batch resumes mid-way
            index.save(str(working_path))
            logging.info(f"  Saved progress | Vectors: {len(index):,}")

        if not working_path.exists():
            # every chunk was empty, so the loop above never saved anything
            index.save(str(working_path))

        index_path = self._finalize_shard(batch, working_path)
        logging.info(f"  Saved {len(index):,} vectors → {index_path}")

    def _load_indexes(self, shard_files: list[Path]) -> list:
        if self.load_mode == "view":
            # a single Indexes object memory-maps and searches all shards for us
            return [Indexes(paths=[str(p) for p in shard_files], view=True)]
        return super()._load_indexes(shard_files)

    def _read_index(self, path: Path):
        """
        Opens a single shard -- memory-mapped in `scan` mode, or copied into RAM
        otherwise. Compressed shards must always be decompressed into RAM.
        """
        if path.suffix == ".zst":
            return Index.restore(self._read_bytes(path))
        if self.load_mode == "scan":
            return Indexes(paths=[str(path)], view=True)
        return Index.restore(str(path))

    @staticmethod
    def _num_vectors(index) -> int:
        return len(index)

    def _search(
        self,
        vec: numpy.ndarray,
        count: int,
    ) -> polars.DataFrame:
        # distances are exact, so shard results can be merged as-is
        keys, distances = [], []
        for index in self._iter_indexes():
            matches = index.search(vec, count)
            keys.extend(matches.keys.tolist())
            distances.extend(matches.distances.tolist())

        return self._hits_dataframe(keys, distances, count)
