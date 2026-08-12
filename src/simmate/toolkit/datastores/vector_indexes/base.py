# -*- coding: utf-8 -*-

import copy
import logging
from pathlib import Path
from typing import Callable

import numpy
import polars
import pyarrow
import zstandard as zstd

from simmate.utils import chunk_list, dispatch, get_directory


class VectorIndex:
    """
    Base class for configuring and managing a vector index backend
    for a datastore column.

    Vectors live as packed bits in a datastore column, and the index is split
    into "shards" -- one index file per batch of datastore chunks. Sharding
    keeps each build step small enough to run (and resume) independently.

    Indexes are declared as shared class attributes (see
    `MoleculeDatastore.vector_indexes`), so a declaration is a *template* that
    must be bound to a datastore before use. `for_datastore` does the binding,
    and `MyDatastore.get_vector_index(name)` is the normal way to get one.

    Subclasses supply the engine-specific pieces: `_build_batch`,
    `_read_index`, `_num_vectors`, and `_search`.
    """

    index_suffix: str = ""
    """
    File extension used for this backend's shards (also the engine's name).
    Set by subclasses.
    """

    valid_load_modes: list[str] = ["memory", "scan", "view"]
    """
    Load modes this backend accepts. `memory` holds all shards in RAM, `scan`
    reads (and releases) one shard at a time during each search, and `view`
    memory-maps the shards so that only the pages a search actually touches are
    ever read in. Subclasses can narrow or extend this list.
    """

    batch_size: int = 1
    """Number of datastore chunks packed into each shard."""

    requires_metric_fn: bool = False
    """
    Whether this backend needs a `metric_fn`. True for engines that search the
    packed bits directly (such as usearch), and False for engines that quantize
    the vectors first (such as faiss).
    """

    def __init__(
        self,
        column_name: str,
        ndim: int,
        featurizer,
        metric_fn: Callable = None,
        featurizer_kwargs: dict = None,
        load_mode: str = "memory",
        compress: bool = False,
    ):
        """
        Args:
            column_name: Datastore column holding the packed-bit vectors.
            ndim: Number of bits in each vector.
            featurizer: Featurizer class that generates the column's vectors.
            metric_fn: Compiled (numba) distance function. Required by engines
                that search the packed bits directly (such as usearch), and
                unused by engines that quantize the vectors first (such as faiss).
            featurizer_kwargs: Extra kwargs passed to the featurizer.
            load_mode: How shards are loaded for search. See `valid_load_modes`.
            compress: Whether `build` writes shards zstd-compressed, which
                trades disk space for decompressing each shard as it is read.
        """
        if load_mode not in self.valid_load_modes:
            raise ValueError(
                f"Unknown load_mode: {load_mode!r}. "
                f"Use one of {self.valid_load_modes}."
            )
        if self.requires_metric_fn and metric_fn is None:
            raise ValueError(
                f"{type(self).__name__} needs a `metric_fn`, because its search "
                "runs on the packed bits directly."
            )

        self.column_name = column_name
        self.ndim = ndim
        self.stored_bytes = ndim // 8
        self.featurizer = featurizer
        self.metric_fn = metric_fn
        self.featurizer_kwargs = featurizer_kwargs or {}
        self.load_mode = load_mode
        self.compress = compress

        self._datastore = None  # set by for_datastore()
        self._reset_caches()

    # -------------------------------------------------------------------------

    # binding to a datastore

    @property
    def datastore(self):
        """The datastore this index reads from. Set via `for_datastore`."""
        if self._datastore is None:
            raise AttributeError(
                f"This {type(self).__name__} is not bound to a datastore. "
                "Use `MyDatastore.get_vector_index(name)` rather than reading "
                "`vector_indexes` directly."
            )
        return self._datastore

    def for_datastore(self, datastore_cls) -> "VectorIndex":
        """
        A copy of this index bound to `datastore_cls`.

        Binding copies rather than mutates, since one declaration is shared by
        every datastore that inherits it -- otherwise two datastores would
        fight over the same caches.
        """
        bound = copy.copy(self)
        bound._datastore = datastore_cls
        bound._reset_caches()
        return bound

    def _reset_caches(self) -> None:
        """
        Clears the datastore-specific caches, so that a newly bound copy never
        inherits the template's, and a rebuilt index is loaded fresh.
        Subclasses extend this with any caches of their own.
        """
        self._shard_paths = None
        self._loaded_indexes = None
        self._loaded_mode = None

    # -------------------------------------------------------------------------

    # shard file naming + discovery

    def vectors_directory(self) -> Path:
        """Directory holding the index shards."""
        return get_directory(self.datastore.base_directory / "vectors")

    def _shard_path(self, batch: list[int], suffix: str = "") -> Path:
        """
        Where one batch's shard is written. `suffix` is appended to the
        filename, and is used for the in-progress (`.partial`) and
        compressed (`.zst`) variants.
        """
        name = f"{self.column_name}-{batch[0]}-{batch[-1]}.{self.index_suffix}"
        return self.vectors_directory() / (name + suffix)

    def _final_shard_path(self, batch: list[int]) -> Path:
        """Where a finished shard lands, which is `.zst` when compression is on."""
        return self._shard_path(batch, ".zst" if self.compress else "")

    def _shard_exists(self, batch: list[int]) -> bool:
        """Whether a batch's shard is built, in either its plain or `.zst` form."""
        return any(self._shard_path(batch, suffix).exists() for suffix in ["", ".zst"])

    def _find_shards(self) -> list[Path]:
        """Sorted shard files for the active engine, ignoring partial writes."""
        pattern = f"{self.column_name}-*.{self.index_suffix}*"
        return sorted(
            p
            for p in self.vectors_directory().glob(pattern)
            if p.is_file() and p.suffix != ".partial"
        )

    # -------------------------------------------------------------------------

    # pulling vectors back out of the datastore

    def _chunk_vectors(self, chunk_key: int) -> polars.LazyFrame:
        """Lazy frame of just the id + vector columns for one chunk_key."""
        partition_dir = self.datastore.live_directory / f"chunk_key={chunk_key}"
        if partition_dir.is_dir():
            lazy_df = polars.scan_parquet(partition_dir / "*.parquet")
        else:
            lazy_df = self.datastore.lf.filter(polars.col("chunk_key") == chunk_key)
        return lazy_df.select("datastore_id", self.column_name)

    def _packed_vectors(self, df: polars.DataFrame) -> numpy.ndarray:
        """
        Converts the packed-bytes vector column into a uint8
        (n_rows, stored_bytes) matrix.
        """
        vectors = (
            df.to_arrow()
            .column(self.column_name)
            .cast(pyarrow.binary(self.stored_bytes))
            .combine_chunks()
        )
        # read the arrow buffer directly (zero-copy) and trim to this column's
        # slice of it, which may start partway in if the frame was sliced
        values = numpy.frombuffer(vectors.buffers()[1], dtype=numpy.uint8)
        start = vectors.offset * self.stored_bytes
        end = start + len(vectors) * self.stored_bytes
        return values[start:end].reshape(-1, self.stored_bytes)

    # -------------------------------------------------------------------------

    # building shards

    def build(self, parallel_job: bool = False) -> None:
        """
        Builds every shard that isn't on disk yet, so interrupted builds can
        simply be re-run to pick up where they left off.
        """
        batches = self._pending_batches()
        if not batches:
            logging.info(f"{self.index_suffix} index is already built!")
            return

        self._prepare_build()
        dispatch(
            batches,
            self._build_batch,
            parallel="job" if parallel_job else "single",
        )
        # any shards loaded earlier are now stale, so the next search reloads
        self._reset_caches()

        # "job" mode only submits the work to the executor
        status = "submitted" if parallel_job else "complete"
        logging.info(f"{self.index_suffix} index build {status}!")

    def _pending_batches(self) -> list[list[int]]:
        """Determines which batches of chunk_keys still need a shard built."""
        chunk_keys = list(range(self.datastore.num_chunks))
        batches = [list(b) for b in chunk_list(chunk_keys, self.batch_size)]
        pending = [b for b in batches if not self._shard_exists(b)]

        logging.info(
            f"{len(batches) - len(pending)} batches already done, "
            f"{len(pending)} to process"
        )
        return pending

    def _prepare_build(self) -> None:
        """
        Hook for one-time setup needed before any shard is built (such as
        training). Only called when there are shards left to build.
        """
        pass  # nothing needed by default

    def _build_batch(self, batch: list[int]) -> None:
        """Builds and saves the single shard covering `batch` of chunk_keys."""
        raise NotImplementedError("Subclasses must implement _build_batch")

    def _finalize_shard(self, batch: list[int], working_path: Path) -> Path:
        """
        Moves a finished `.partial` shard into place, compressing it first when
        `compress` is on. The compressed copy goes to another temp file so that
        an interrupted write is never mistaken for a completed shard.
        """
        index_path = self._final_shard_path(batch)
        if not self.compress:
            working_path.replace(index_path)
            return index_path

        compressed_path = self._shard_path(batch, ".zst.partial")
        self._write_zstd(working_path.read_bytes(), compressed_path)
        compressed_path.replace(index_path)
        working_path.unlink()
        return index_path

    # -------------------------------------------------------------------------

    # loading + searching shards

    def load(self) -> None:
        """
        Prepares the shards for searching, per `load_mode`. Results are cached
        on this object, so repeat calls are free until `load_mode` changes.
        """
        if self._loaded_mode == self.load_mode:
            return

        shard_files = self._find_shards()
        if not shard_files:
            raise FileNotFoundError(
                f"No {self.column_name} {self.index_suffix} shard files found in "
                f"{self.vectors_directory()}. Run build() first."
            )
        if self.load_mode == "view" and any(p.suffix == ".zst" for p in shard_files):
            raise ValueError(
                f"The {self.column_name} shards are zstd-compressed, which cannot "
                "be memory-mapped. Use load_mode 'memory' or 'scan'."
            )

        logging.info(
            f"Loading {len(shard_files)} {self.column_name} {self.index_suffix} "
            f"shard(s) in {self.load_mode!r} mode..."
        )
        self._shard_paths = shard_files
        if self.load_mode == "scan":
            # scan defers reading until each shard is actually searched, and so
            # also drops any shards an earlier load_mode left in RAM
            self._loaded_indexes = None
        else:
            self._loaded_indexes = self._load_indexes(shard_files)
            num_vectors = sum(self._num_vectors(i) for i in self._loaded_indexes)
            logging.info(f"Loaded {num_vectors:,} vectors.")
        # set last, so a failed load is never mistaken for a cached one
        self._loaded_mode = self.load_mode

    def _load_indexes(self, shard_files: list[Path]) -> list:
        """Reads the shard files into the index objects that `search` will use."""
        return [self._read_index(path) for path in shard_files]

    def _read_index(self, path: Path):
        """Reads a single shard from disk into an engine index object."""
        raise NotImplementedError("Subclasses must implement _read_index")

    @staticmethod
    def _num_vectors(index) -> int:
        """Number of vectors held by one loaded shard."""
        raise NotImplementedError("Subclasses must implement _num_vectors")

    def _iter_indexes(self):
        """
        Yields each shard to search. In `scan` mode, shards are read from disk
        one at a time and released instead of being kept in RAM.
        """
        if self.load_mode == "scan":
            for path in self._shard_paths:
                yield self._read_index(path)
        else:
            yield from self._loaded_indexes

    def search(
        self,
        vec: numpy.ndarray,
        count: int = 50,
    ) -> polars.DataFrame:
        """
        Finds the `count` closest vectors to `vec`.

        Returns:
            A `datastore_id` + `distance` dataframe, sorted closest-first.
        """
        self.load()
        return self._search(vec, count)

    def _search(
        self,
        vec: numpy.ndarray,
        count: int,
    ) -> polars.DataFrame:
        """Engine-specific half of `search`, called once the shards are loaded."""
        raise NotImplementedError("Subclasses must implement _search")

    @staticmethod
    def _hits_dataframe(datastore_ids, distances, count: int) -> polars.DataFrame:
        """The shared return shape of `search`: top-k hits sorted by distance."""
        return (
            polars.DataFrame(
                {"datastore_id": datastore_ids, "distance": distances},
                schema={"datastore_id": polars.Int64, "distance": polars.Float32},
            )
            .sort("distance")
            .head(count)
        )

    # -------------------------------------------------------------------------

    # (de)compression helpers

    @staticmethod
    def _read_bytes(path: Path) -> bytes:
        """Reads bytes from a file, decompressing if it has a .zst suffix."""
        if path.suffix == ".zst":
            return zstd.ZstdDecompressor().decompress(path.read_bytes())
        return path.read_bytes()

    @staticmethod
    def _write_zstd(data: bytes, path: Path) -> None:
        """Writes bytes to a file, compressed with zstd."""
        path.write_bytes(zstd.ZstdCompressor().compress(data))
