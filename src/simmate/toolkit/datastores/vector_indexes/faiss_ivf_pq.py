# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import faiss
import numpy
import polars

from simmate.toolkit.similarity import Tanimoto

from .base import VectorIndex


class FaissIvfPqIndex(VectorIndex):
    """
    IVF coarse clustering + product quantization. Each vector compresses to
    ``m`` bytes, so indexes are far smaller than HNSW, at the cost of
    approximate recall. Returned distances are still exact Tanimoto
    (candidates get reranked). Note that `metric_fn` is unused here, because the
    quantized codes are searched by faiss itself.

    For trillion-scale datastores the shards outgrow RAM long before they
    outgrow disk, so `view` mode maps them instead of copying them in. What
    stays resident is then only the per-shard IVF overhead (the coarse
    centroids, the PQ codebook, and the precomputed distance table), rather
    than the ``m + 8`` bytes of codes and ids held for every vector.
    """

    index_suffix: str = "faiss"

    batch_size: int = 200
    """
    Number of datastore chunks packed into each shard. Larger than the base
    default because each vector compresses to only `m` bytes, so a shard can
    absorb far more chunks before it gets unwieldy.
    """

    nlist: int = 4096
    """Number of IVF clusters (coarse centroids) per shard."""

    m: int = 8
    """
    Number of sub-vectors each vector is quantized into, which is also its
    compressed size in bytes. Must divide `ndim`.
    """

    nbits: int = 8
    """Bits per sub-vector code (8 gives 256 centroids each)."""

    nprobe: int = 16
    """Number of clusters visited per query. Higher = better recall, slower search."""

    use_mapped_reader: bool = True
    """
    Whether mapped reads go through faiss's `MappedFileIOReader`
    (`IO_FLAG_MMAP_IFC`) rather than its older `IO_FLAG_MMAP` path. The mapped
    reader also maps the coarse centroids, and is the only one of the two
    compiled into the Windows faiss wheels. `IO_FLAG_MMAP` maps just the
    inverted lists, and is the longer-standing option on linux.
    """

    skip_precompute_table: bool = False
    """
    Whether to skip building the IVF+PQ precomputed distance table when a shard
    is read. The table is `nlist * m * 2**nbits * 4` bytes of *resident* RAM per
    shard, which is what dominates `view` mode's memory use, so skipping it
    trades search speed for a much smaller footprint.
    """

    train_size: int = 250_000
    """Number of vectors sampled to train the shared IVF+PQ template."""

    add_batch_size: int = 250_000
    """Number of rows unpacked into RAM at a time while filling a shard."""

    max_training_files: int = 100
    """Cap on how many chunk files the training set is sampled from."""

    rerank_multiplier: int = 4
    """
    How many extra candidates each search pulls per requested hit, before they
    are reranked on their exact Tanimoto distance. Higher = better recall,
    but more full vectors read back out of the datastore.
    """

    def _reset_caches(self) -> None:
        super()._reset_caches()
        self._cached_template = None

    def _unpacked_vectors(self, df: polars.DataFrame) -> numpy.ndarray:
        """
        Converts the packed-bytes vector column into a float32
        (n_rows, ndim) matrix of 1s and 0s, which is the format faiss expects.
        """
        return numpy.unpackbits(self._packed_vectors(df), axis=1).astype(numpy.float32)

    # -------------------------------------------------------------------------

    # training the template index shared by all shards

    def _template_file(self) -> Path:
        """Path of the trained-but-empty IVF+PQ index shared by all shards."""
        return self.vectors_directory() / f"{self.column_name}.template.faiss"

    def _training_set_file(self) -> Path:
        """
        Path of the parquet file holding the training vectors. If this file
        exists it is used as-is; otherwise vectors are sampled from the data
        chunks and saved here for reproducibility.
        """
        return self.vectors_directory() / f"{self.column_name}.training.parquet"

    def _template(self):
        """The trained-but-empty template index, read from disk once per process."""
        if self._cached_template is None:
            self._cached_template = faiss.read_index(str(self._template_file()))
        return self._cached_template

    def train_template(self, rebuild: bool = False) -> Path:
        """Trains (and saves) the template index, unless one already exists."""
        template_file = self._template_file()
        if template_file.exists() and not rebuild:
            return template_file

        if self.ndim % self.m != 0:
            raise ValueError(
                f"m ({self.m}) must divide the {self.column_name} ndim ({self.ndim})."
            )

        vectors = self._sample_training_vectors()
        if len(vectors) < 39 * self.nlist:
            logging.warning(
                f"Only {len(vectors):,} training vectors for nlist={self.nlist} "
                f"(faiss wants >= {39 * self.nlist:,}). Consider lowering nlist."
            )

        logging.info(
            f"Training {self.column_name} IVF+PQ on {len(vectors):,} vectors | "
            f"nlist={self.nlist}, m={self.m}, nbits={self.nbits}"
        )
        index = faiss.IndexIVFPQ(
            faiss.IndexFlatL2(self.ndim),
            self.ndim,
            self.nlist,
            self.m,
            self.nbits,
        )
        index.train(vectors)

        faiss.write_index(index, str(template_file))
        # dropped so that `build` can pickle this object (and its bound
        # `_build_batch`) out to parallel workers -- a faiss index cannot be
        # pickled, and each worker reads the template from disk anyway
        self._cached_template = None
        logging.info(f"Saved training template → {template_file}")
        return template_file

    def _sample_training_vectors(self) -> numpy.ndarray:
        """
        Loads the saved training set, or creates one by sampling vectors evenly
        across the datastore's chunk files.
        """
        training_file = self._training_set_file()
        if training_file.exists():
            logging.info(f"Loading training set from {training_file}")
            return self._unpacked_vectors(polars.read_parquet(training_file))

        chunk_files = self.datastore.chunk_files[: self.max_training_files]
        if not chunk_files:
            raise FileNotFoundError(
                f"{self.datastore.datastore_name} has no chunk files to sample "
                f"{self.column_name} training vectors from."
            )
        rows_per_file = max(self.train_size // len(chunk_files), 1)
        samples = []
        for file in chunk_files:
            df = polars.read_parquet(file, columns=[self.column_name])
            # small chunk files may not have enough rows to give a full sample
            samples.append(df.sample(n=min(rows_per_file, len(df))))
        training_df = polars.concat(samples)

        training_df.write_parquet(training_file)
        logging.info(f"Saved {len(training_df):,} training vectors → {training_file}")
        return self._unpacked_vectors(training_df)

    # -------------------------------------------------------------------------

    # building shards

    def _prepare_build(self) -> None:
        self.train_template()

    def _build_batch(self, batch: list[int]) -> None:
        logging.info(
            f"Building {self.column_name} batch {batch[0]}-{batch[-1]} → "
            f"{self._final_shard_path(batch)}"
        )

        index = faiss.clone_index(self._template())
        for chunk_key in batch:
            logging.info(f"  {self.column_name} chunk_key={chunk_key}")
            num_added = 0
            for df in self._iter_row_batches(chunk_key):
                index.add_with_ids(
                    self._unpacked_vectors(df),
                    df["datastore_id"].to_numpy().astype(numpy.int64),
                )
                num_added += len(df)
            logging.info(f"  Added {num_added:,} | Vectors: {index.ntotal:,}")

        # written to a temp file first so that an interrupted write is never
        # mistaken for a completed shard
        temp_path = self._shard_path(batch, ".partial")
        faiss.write_index(index, str(temp_path))
        index_path = self._finalize_shard(batch, temp_path)
        logging.info(f"  Saved {index.ntotal:,} vectors → {index_path}")

    def _iter_row_batches(self, chunk_key: int):
        """
        Yields one chunk's rows in dataframes of at most `add_batch_size` rows,
        so that a full chunk never has to be unpacked into RAM at once.
        """
        lazy_df = self._chunk_vectors(chunk_key)
        offset = 0
        while True:
            df = lazy_df.slice(offset, self.add_batch_size).collect()
            if df.is_empty():
                return
            yield df
            offset += len(df)

    # -------------------------------------------------------------------------

    # loading + searching shards

    def _read_index(self, path: Path):
        """
        Opens a single shard -- memory-mapped in `view` and `scan` modes, or
        copied into RAM otherwise. Compressed shards must always be
        decompressed into RAM.
        """
        if path.suffix == ".zst":
            raw = self._read_bytes(path)
            index = faiss.deserialize_index(numpy.frombuffer(raw, dtype=numpy.uint8))
        elif self.load_mode in ["view", "scan"]:
            index = self._read_index_mapped(path)
        else:
            index = faiss.read_index(str(path), faiss.IO_FLAG_READ_ONLY)
        index.nprobe = self.nprobe
        return index

    def _read_index_mapped(self, path: Path):
        """
        Reads a shard without copying it into RAM. faiss maps the file and
        points the index's code and id arrays straight at the mapping, so only
        the pages a search actually touches are ever paged in.
        """
        flags = faiss.IO_FLAG_READ_ONLY
        if self.skip_precompute_table:
            flags |= faiss.IO_FLAG_SKIP_PRECOMPUTE_TABLE

        if self.use_mapped_reader:
            owner = faiss.MmappedFileMappingOwner(str(path))
            reader = faiss.MappedFileIOReader(owner)
            index = faiss.read_index(reader, flags | faiss.IO_FLAG_MMAP_IFC)
            # the index holds views into the mapping rather than its own copy,
            # so the mapping has to outlive it
            index._mapping_refs = (owner, reader)
        else:
            index = faiss.read_index(str(path), flags | faiss.IO_FLAG_MMAP)

        if self.skip_precompute_table:
            # the shard was trained with the table on, so its "use the table"
            # flag is saved as set. Without clearing it, the search would index
            # into a table that was never filled in.
            index.use_precomputed_table = 0
        return index

    @staticmethod
    def _num_vectors(index) -> int:
        return index.ntotal

    def _search(
        self,
        vec: numpy.ndarray,
        count: int,
    ) -> polars.DataFrame:
        """
        IVF+PQ distances are approximate, so extra candidates are pulled from
        each shard and then reranked on their exact Tanimoto distance.
        """
        num_candidates = count * self.rerank_multiplier
        query_vector = numpy.unpackbits(vec).astype(numpy.float32)[None, :]

        keys = self._candidate_keys(query_vector, num_candidates)
        if len(keys) == 0:
            return self._hits_dataframe([], [], count)

        df = (
            self.datastore.filter(datastore_id__in=numpy.unique(keys).tolist())
            .select("datastore_id", self.column_name)
            .collect()
        )
        return self._hits_dataframe(
            df["datastore_id"].to_numpy().astype(numpy.int64),
            Tanimoto.get_distance_packed(vec, self._packed_vectors(df)),
            count,
        )

    def _candidate_keys(
        self,
        query_vector: numpy.ndarray,
        num_candidates: int,
    ) -> numpy.ndarray:
        """
        The `num_candidates` datastore_ids closest to `query_vector` by their
        approximate (quantized) distance, gathered from every shard.
        """
        keys, pq_distances = [], []
        for index in self._iter_indexes():
            shard_distances, shard_keys = index.search(query_vector, num_candidates)
            keys.append(shard_keys[0])
            pq_distances.append(shard_distances[0])
        keys = numpy.concatenate(keys)
        pq_distances = numpy.concatenate(pq_distances)

        # shards pad their results with -1 when they have too few vectors
        found = keys != -1
        keys, pq_distances = keys[found], pq_distances[found]

        # trim to the best candidates across all shards before the rerank,
        # which needs to read each candidate's full vector back out
        if len(keys) > num_candidates:
            closest = numpy.argpartition(pq_distances, num_candidates)[:num_candidates]
            keys = keys[closest]
        return keys
