# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import polars
import pyarrow

from simmate.utils import get_directory


class VectorIndex:
    """
    Base class for configuring and managing a vector index backend
    for a datastore column.
    """

    index_suffix: str = ""  # Set by subclasses

    def __init__(
        self,
        column_name: str,
        batch_size: int = 1,
        load_mode: str = "memory",
    ):
        self.column_name = column_name
        self.batch_size = batch_size
        self.load_mode = load_mode

        self._cached_payload = None
        self._cached_mode = None

    def vectors_directory(self, datastore_cls) -> Path:
        """Directory holding the fingerprint index shards."""
        return get_directory(datastore_cls.base_directory / "vectors")

    def _use_zstd(self) -> bool:
        """Whether shards are written zstd-compressed."""
        return self.load_mode == "scan-zstd"

    def _shard_paths(self, datastore_cls, batch: list[int]) -> tuple[Path, Path]:
        """
        The ``(uncompressed, final)`` shard paths for one batch of chunk_keys.
        """
        uncompressed = self.vectors_directory(datastore_cls) / self._shard_name(batch)
        if not self._use_zstd():
            return uncompressed, uncompressed
        return uncompressed, self._add_suffix(uncompressed, ".zst")

    def _shard_name(self, batch: list[int]) -> str:
        """Filename of one batch's uncompressed shard."""
        return f"{self.column_name}-{batch[0]}-{batch[-1]}.{self.index_suffix}"

    @staticmethod
    def _add_suffix(path: Path, suffix: str) -> Path:
        """Appends a suffix rather than replacing the existing one."""
        return path.with_suffix(path.suffix + suffix)

    def _built_shard_names(self, datastore_cls) -> set[str]:
        """Names of every shard already on disk, for resume checks."""
        return {
            p.name
            for p in self.vectors_directory(datastore_cls).glob(f"{self.column_name}-*")
        }

    def _shard_exists(self, datastore_cls, batch: list[int]) -> bool:
        """Whether a batch's shard is already built."""
        name = self._shard_name(batch)
        built = self._built_shard_names(datastore_cls)
        return name in built or f"{name}.zst" in built

    def _index_files(self, datastore_cls) -> list[Path]:
        """Sorted index shard files for the active engine."""
        pattern = f"{self.column_name}-*.{self.index_suffix}*"
        return sorted(
            p
            for p in self.vectors_directory(datastore_cls).glob(pattern)
            if p.is_file() and p.suffix != ".partial"
        )

    def _chunk_vectors(self, datastore_cls, chunk_key: int) -> polars.LazyFrame:
        """Lazy frame of just the id + fingerprint columns for one chunk_key."""
        partition_dir = datastore_cls.live_directory / f"chunk_key={chunk_key}"
        if partition_dir.is_dir():
            lazy_df = polars.scan_parquet(partition_dir / "*.parquet")
        else:
            lazy_df = datastore_cls.lf.filter(polars.col("chunk_key") == chunk_key)
        return lazy_df.select("datastore_id", self.column_name)

    def _packed_vectors(self, datastore_cls, df: polars.DataFrame) -> numpy.ndarray:
        """
        Converts a fingerprint column of packed bytes into a uint8
        (n_rows, stored_bytes) matrix.
        """
        stored_bytes = datastore_cls._VECTOR_CONFIGS[self.column_name]["stored_bytes"]
        fps = (
            df.to_arrow()
            .column(self.column_name)
            .cast(pyarrow.binary(stored_bytes))
            .combine_chunks()
        )
        values = numpy.frombuffer(fps.buffers()[1], dtype=numpy.uint8)
        start = fps.offset * stored_bytes
        return values[start : start + len(fps) * stored_bytes].reshape(-1, stored_bytes)

    def _unpacked_vectors(self, datastore_cls, df: polars.DataFrame) -> numpy.ndarray:
        """
        Converts a fingerprint column of packed bytes into the float32
        (n_rows, ndim) matrix that faiss expects.
        """
        packed = self._packed_vectors(datastore_cls, df)
        return numpy.unpackbits(packed, axis=1).astype(numpy.float32)

    @staticmethod
    def _hits_dataframe(datastore_ids, distances, count: int) -> polars.DataFrame:
        """The shared return shape of every search method: top-k hits sorted by distance."""
        return (
            polars.DataFrame(
                {"datastore_id": datastore_ids, "distance": distances},
                schema={"datastore_id": polars.Int64, "distance": polars.Float32},
            )
            .sort("distance")
            .head(count)
        )

    @staticmethod
    def _tanimoto_distances(
        query: numpy.ndarray,
        candidates: numpy.ndarray,
    ) -> numpy.ndarray:
        """
        Tanimoto distance between one packed query fingerprint and a
        (n_candidates, stored_bytes) matrix of packed fingerprints.
        """
        intersection = numpy.bitwise_count(query & candidates).sum(axis=1)
        union = numpy.bitwise_count(query | candidates).sum(axis=1)
        with numpy.errstate(invalid="ignore", divide="ignore"):
            similarity = numpy.where(union > 0, intersection / union, 0.0)
        return (1 - similarity).astype(numpy.float32)

    def build(self, datastore_cls, parallel_job: bool = False):
        raise NotImplementedError

    def load(self, datastore_cls):
        raise NotImplementedError

    def search(self, datastore_cls, vec: numpy.ndarray, count: int):
        raise NotImplementedError
