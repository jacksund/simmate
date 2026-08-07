# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import faiss
import numpy
import polars
import zstandard as zstd

from simmate.utils import chunk_list, dispatch

from .base import VectorIndex


class FaissIvfPqIndex(VectorIndex):
    """
    IVF coarse clustering + product quantization. Each
    vector compresses to ``m`` bytes, so indexes are far
    smaller than HNSW, at the cost of approximate recall. Returned distances
    are still exact Tanimoto (candidates get reranked). Requires the optional
    ``faiss-cpu`` package.
    """

    index_suffix: str = "faiss"

    def __init__(
        self,
        column_name: str,
        batch_size: int = 1,
        load_mode: str = "memory",
        nlist: int = 4096,
        m: int = 8,
        nbits: int = 8,
        nprobe: int = 16,
    ):
        super().__init__(column_name, batch_size, load_mode)
        self.nlist = nlist
        self.m = m
        self.nbits = nbits
        self.nprobe = nprobe
        self._faiss_template_obj = None

    def _faiss_template_file(self, datastore_cls) -> Path:
        """
        Path of the trained-but-empty IVF+PQ index shared by all shards.
        """
        return (
            self.vectors_directory(datastore_cls) / f"{self.column_name}.template.faiss"
        )

    def _faiss_template(self, datastore_cls):
        """
        The trained-but-empty template index, read from disk once per process.
        """
        if self._faiss_template_obj is None:
            path = self._faiss_template_file(datastore_cls)
            self._faiss_template_obj = faiss.read_index(str(path))
        return self._faiss_template_obj

    def train_faiss_template(self, datastore_cls, rebuild: bool = False):
        template_file = self._faiss_template_file(datastore_cls)
        if template_file.exists() and not rebuild:
            return template_file

        ndim = datastore_cls._VECTOR_CONFIGS[self.column_name]["ndim"]
        if ndim % self.m != 0:
            raise ValueError(
                f"faiss_settings['m'] ({self.m}) must divide the {self.column_name} ndim ({ndim})."
            )

        vectors = self._sample_training_vectors(datastore_cls)
        if len(vectors) < 39 * self.nlist:
            logging.warning(
                f"Only {len(vectors):,} training vectors for nlist={self.nlist} "
                f"(faiss wants >= {39 * self.nlist:,}). Lower nlist in faiss_settings."
            )

        logging.info(
            f"Training {self.column_name} IVF+PQ on {len(vectors):,} vectors | "
            f"nlist={self.nlist}, m={self.m}, nbits={self.nbits}"
        )
        index = faiss.IndexIVFPQ(
            faiss.IndexFlatL2(ndim), ndim, self.nlist, self.m, self.nbits
        )
        index.train(vectors)

        faiss.write_index(index, str(template_file))
        self._faiss_template_obj = None
        logging.info(f"Saved training template → {template_file}")
        return template_file

    def _sample_training_vectors(self, datastore_cls) -> numpy.ndarray:
        train_size = 250_000
        max_files = 64

        chunk_files = datastore_cls.chunk_files
        if not chunk_files:
            raise FileNotFoundError(
                f"No parquet files found in {datastore_cls.live_directory}. "
                "Nothing to train an index on."
            )

        if len(chunk_files) > max_files:
            step = len(chunk_files) / max_files
            chunk_files = [chunk_files[int(i * step)] for i in range(max_files)]

        rows_per_file = max(1, train_size // len(chunk_files))
        frames = []
        for file in chunk_files:
            df = polars.read_parquet(
                file, columns=[self.column_name], n_rows=rows_per_file
            )
            if len(df) > 0:
                frames.append(df)

        return self._unpacked_vectors(datastore_cls, polars.concat(frames))

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

        if batches_to_process:
            self.train_faiss_template(datastore_cls)

        dispatch(
            batches_to_process,
            self._build_batch,
            parallel="job" if parallel_job else "single",
            datastore_cls=datastore_cls,
        )
        logging.info("faiss-ivfpq index build complete!")

    def _build_batch(self, batch: list[int], datastore_cls):
        uncompressed_path, index_path = self._shard_paths(datastore_cls, batch)
        logging.info(
            f"Building {self.column_name} batch {batch[0]}-{batch[-1]} → {index_path}"
        )

        index = faiss.clone_index(self._faiss_template(datastore_cls))

        add_batch_size = 250_000

        for chunk_key in batch:
            logging.info(f"  {self.column_name} chunk_key={chunk_key}")
            lazy_df = self._chunk_vectors(datastore_cls, chunk_key)
            offset = 0
            while True:
                df = lazy_df.slice(offset, add_batch_size).collect()
                if len(df) == 0:
                    break
                index.add_with_ids(
                    self._unpacked_vectors(datastore_cls, df),
                    df["datastore_id"].to_numpy().astype(numpy.int64),
                )
                offset += len(df)
            logging.info(f"  Added {offset:,} | Vectors: {index.ntotal:,}")

        temp_path = self._add_suffix(uncompressed_path, ".partial")
        if self._use_zstd():
            raw = faiss.serialize_index(index).tobytes()
            temp_path.write_bytes(zstd.ZstdCompressor().compress(raw))
        else:
            faiss.write_index(index, str(temp_path))
        temp_path.replace(index_path)
        logging.info(f"  Saved {index.ntotal:,} vectors → {index_path}")

    def load(self, datastore_cls) -> None:
        if self._cached_payload is not None and self._cached_mode == self.load_mode:
            return

        mode = self.load_mode
        if mode not in ["memory", "scan", "scan-zstd"]:
            raise ValueError(
                f"Unknown load_mode: {mode!r}. " "Use 'memory', 'scan', or 'scan-zstd'."
            )

        index_files = self._index_files(datastore_cls)
        if not index_files:
            raise FileNotFoundError(
                f"No {self.column_name} faiss index files found in "
                f"{self.vectors_directory(datastore_cls)}. "
                "Run build() first."
            )

        n_files = f"{len(index_files)} {self.column_name} faiss index file(s)"
        if mode == "memory":
            logging.info(f"Loading {n_files} into RAM...")
            payload = [self._read_index(p) for p in index_files]
            n_vectors = sum(i.ntotal for i in payload)
            logging.info(f"Loaded {n_vectors:,} vectors.")
        else:
            logging.info(f"Registering {n_files} for scan-mode search.")
            payload = index_files

        self._cached_mode = mode
        self._cached_payload = payload

    def _read_index(self, path: Path):
        is_zstd = path.suffix == ".zst"
        raw = zstd.ZstdDecompressor().decompress(path.read_bytes()) if is_zstd else None

        index = (
            faiss.deserialize_index(numpy.frombuffer(raw, dtype=numpy.uint8))
            if is_zstd
            else faiss.read_index(str(path), faiss.IO_FLAG_READ_ONLY)
        )
        index.nprobe = self.nprobe
        return index

    def _iter_indexes(self):
        if self._cached_mode == "memory":
            return self._cached_payload
        return (self._read_index(path) for path in self._cached_payload)

    def search(self, datastore_cls, vec: numpy.ndarray, count: int = 50):
        self.load(datastore_cls)

        n_candidates = count * 4
        query_vector = numpy.unpackbits(vec).astype(numpy.float32)[None, :]

        keys, pq_distances = [], []
        for index in self._iter_indexes():
            shard_distances, shard_keys = index.search(query_vector, n_candidates)
            keys.append(shard_keys[0])
            pq_distances.append(shard_distances[0])

        keys = numpy.concatenate(keys)
        pq_distances = numpy.concatenate(pq_distances)

        found = keys != -1
        keys, pq_distances = keys[found], pq_distances[found]
        if len(keys) == 0:
            return self._hits_dataframe([], [], count)

        if len(keys) > n_candidates:
            closest = numpy.argpartition(pq_distances, n_candidates)[:n_candidates]
            keys = keys[closest]

        candidate_ids = numpy.unique(keys)
        df = (
            datastore_cls.filter(datastore_id__in=candidate_ids.tolist())
            .select("datastore_id", self.column_name)
            .collect()
        )
        return self._hits_dataframe(
            df["datastore_id"].to_numpy().astype(numpy.int64),
            self._tanimoto_distances(vec, self._packed_vectors(datastore_cls, df)),
            count,
        )
