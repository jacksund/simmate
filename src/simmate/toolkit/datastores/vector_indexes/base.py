# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import polars
import pyarrow
import zstandard as zstd

from simmate.utils import chunk_list, get_directory


class VectorIndex:
    """
    Base class for configuring and managing a vector index backend
    for a datastore column.
    """

    index_suffix: str = ""  # Set by subclasses
    valid_load_modes: list[str] = ["memory", "scan", "scan-zstd"]  # Set by subclasses

    def __init__(
        self,
        column_name: str,
        ndim: int,
        metric_fn,
        featurizer,
        featurizer_kwargs: dict = None,
        batch_size: int = 1,
        load_mode: str = "memory",
    ):
        self.column_name = column_name
        self.ndim = ndim
        self.stored_bytes = ndim // 8
        self.metric_fn = metric_fn
        self.featurizer = featurizer
        self.featurizer_kwargs = featurizer_kwargs or {}
        self.batch_size = batch_size
        self.load_mode = load_mode

        self._cached_payload = None
        self._cached_mode = None

    def vectors_directory(self, datastore_cls) -> Path:
        """Directory holding the fingerprint index shards."""
        return get_directory(datastore_cls.base_directory / "vectors")

    @property
    def use_zstd(self) -> bool:
        """Whether shards are written zstd-compressed."""
        return self.load_mode == "scan-zstd"

    def _shard_paths(self, datastore_cls, batch: list[int]) -> tuple[Path, Path]:
        """
        The ``(uncompressed, final)`` shard paths for one batch of chunk_keys.
        """
        uncompressed = self.vectors_directory(datastore_cls) / self._shard_name(batch)
        if not self.use_zstd:
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

    def _get_pending_batches(self, datastore_cls) -> list[list[int]]:
        """Calculates which batches of chunks still need to be built."""
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
        return batches_to_process

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
        fps = (
            df.to_arrow()
            .column(self.column_name)
            .cast(pyarrow.binary(self.stored_bytes))
            .combine_chunks()
        )
        values = numpy.frombuffer(fps.buffers()[1], dtype=numpy.uint8)
        start = fps.offset * self.stored_bytes
        return values[start : start + len(fps) * self.stored_bytes].reshape(
            -1, self.stored_bytes
        )

    def _unpacked_vectors(self, datastore_cls, df: polars.DataFrame) -> numpy.ndarray:
        """
        Converts a fingerprint column of packed bytes into the float32
        (n_rows, ndim) matrix that faiss expects.
        """
        packed = self._packed_vectors(datastore_cls, df)
        return numpy.unpackbits(packed, axis=1).astype(numpy.float32)

    def build(self, datastore_cls, parallel_job: bool = False):
        raise NotImplementedError

    def _load_payload(self, index_files: list[Path], n_files_str: str):
        """Loads index files using subclass-specific logic."""
        raise NotImplementedError

    def load(self, datastore_cls) -> None:
        if self._cached_payload is not None and self._cached_mode == self.load_mode:
            return

        mode = self.load_mode
        if mode not in self.valid_load_modes:
            raise ValueError(
                f"Unknown load_mode: {mode!r}. " f"Use one of {self.valid_load_modes}."
            )

        index_files = self._index_files(datastore_cls)
        if not index_files:
            raise FileNotFoundError(
                f"No {self.column_name} {self.index_suffix} index files found in "
                f"{self.vectors_directory(datastore_cls)}. "
                "Run build() first."
            )

        n_files_str = (
            f"{len(index_files)} {self.column_name} {self.index_suffix} index file(s)"
        )
        self._cached_payload = self._load_payload(index_files, n_files_str)
        self._cached_mode = mode

    def search(self, datastore_cls, vec: numpy.ndarray, count: int):
        raise NotImplementedError

    @staticmethod
    def _read_bytes(path: Path) -> bytes:
        """Reads bytes from a file, decompressing if it has a .zst suffix."""
        if path.suffix == ".zst":
            return zstd.ZstdDecompressor().decompress(path.read_bytes())
        return path.read_bytes()

    @staticmethod
    def _write_bytes(data: bytes, path: Path, use_zstd: bool = False):
        """Writes bytes to a file, optionally compressing with zstd."""
        if use_zstd:
            path.write_bytes(zstd.ZstdCompressor().compress(data))
        else:
            path.write_bytes(data)


def get_hits_dataframe(datastore_ids, distances, count: int) -> polars.DataFrame:
    """The shared return shape of every search method: top-k hits sorted by distance."""
    return (
        polars.DataFrame(
            {"datastore_id": datastore_ids, "distance": distances},
            schema={"datastore_id": polars.Int64, "distance": polars.Float32},
        )
        .sort("distance")
        .head(count)
    )
