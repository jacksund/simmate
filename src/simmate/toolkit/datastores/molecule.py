# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import polars
import pyarrow
import zstandard as zstd
from usearch.index import (
    CompiledMetric,
    Index,
    Indexes,
    MetricKind,
    MetricSignature,
    ScalarKind,
)

from simmate.toolkit import Molecule
from simmate.utils import chunk_list, dispatch, filter_polars_df, get_directory

from ..dataframes import MoleculeDataFrame
from ..featurizers import (
    Ecfp4Fingerprint,
    Fcfp4Fingerprint,
    MaccsFingerprint,
    MethodCaller,
    PatternFingerprint,
    PropertyGrabber,
    USearchFingerprints,
)
from ..filters import RemoveInvalidSmiles
from .base import Datastore
from .numba_funcs import tanimoto_ecfp4, tanimoto_ecfp4_1024, tanimoto_maccs
from .utils import update_column, update_table


class MoleculeDatastore(Datastore):
    """
    Base class for molecule-focused datastores. Extends Datastore with
    methods for computing molecular properties, fingerprints, and building
    similarity search indexes.
    """

    @classmethod
    def filter_to_mdf(
        cls,
        similarity=None,
        similarity_count: int = 50,
        similarity_type: str = "ecfp4",
        smarts: list = None,
        limit: int = None,
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
        parallel: bool = False,
        **kwargs,
    ) -> MoleculeDataFrame:
        """
        Filter the datastore and return a MoleculeDataFrame.

        Applies django-style column filters (``**kwargs``) and an optional row
        limit, then returns the result as a ``MoleculeDataFrame``. When
        ``similarity`` is given, runs an ANN search via the fingerprint index
        and joins a ``distance`` column (ascending) into the result.

        Args:
            similarity: Query molecule (``Molecule`` or SMILES) for similarity
                search.
            similarity_count: Number of top similar molecules to retrieve.
            similarity_type: Fingerprint type for similarity search.
                One of ``"ecfp4"``, ``"maccs"``, or ``"fcfp4"``.
            smarts: Not yet implemented — raises ``NotImplementedError``.
            limit: Maximum number of rows to return (ignored when ``similarity``
                is provided).
            init_toolkit_objs: Pre-initialize RDKit Molecule objects in the MDF.
            init_substructure_lib: Pre-initialize substructure library in the MDF.
            init_morgan_fp_lib: Pre-initialize Morgan fingerprint library in the MDF.
            parallel: Use parallel processing in MoleculeDataFrame initialization.
            **kwargs: Django-style column filters (e.g. ``MW__lte=500``).

        Returns:
            MoleculeDataFrame filtered to matching rows.
        """

        if smarts:
            raise NotImplementedError(
                "SMARTS substructure filtering is not yet implemented."
            )

        if similarity:
            sim_df = cls.search_similar(similarity, similarity_count, similarity_type)
            # cls.filter prunes the scan to the hit ids' chunk files, rather than
            # scanning every chunk in the datastore to find a handful of rows
            lazy_df = cls.filter(datastore_id__in=sim_df["datastore_id"].to_list())
        else:
            lazy_df = cls.lf

        if kwargs:
            lazy_df = filter_polars_df(lazy_df, **kwargs)
        if limit and not similarity:
            lazy_df = lazy_df.limit(limit)

        logging.info("Loading from datastore...")
        df = lazy_df.collect()
        if similarity:
            df = df.join(sim_df, on="datastore_id", how="left").sort("distance")

        return MoleculeDataFrame.from_polars(
            df,
            init_toolkit_objs=init_toolkit_objs,
            init_substructure_lib=init_substructure_lib,
            init_morgan_fp_lib=init_morgan_fp_lib,
            parallel=parallel,
        )

    # -------------------------------------------------------------------------

    # helper methods for data cleaning + populating columns

    @update_table()
    def remove_invalid_smiles(cls, df: polars.DataFrame):
        """
        Drops rows with invalid SMILES from each chunk.
        Run before any featurization steps to ensure clean input.
        """

        is_valid = RemoveInvalidSmiles.filter(
            molecules=df["smiles"].to_list(),
            return_mode="booleans",
            parallel=True,
        )
        num_failed = len(is_valid) - sum(is_valid)
        if num_failed > 0:
            logging.warning(f"Removed {num_failed} invalid molecules.")
        return df.filter(is_valid)

    @update_table()
    def add_property_columns(
        cls,
        df: polars.DataFrame,
        properties: list[str] = [
            "molecular_weight_exact",
            "num_atoms_heavy",
            "num_stereocenters",
            "num_h_acceptors",
            "num_h_donors",
            "log_p_rdkit",
            "synthetic_accessibility",
        ],
    ):
        """
        Computes physicochemical properties and adds them as columns.
        Defaults to the classic Lipinski-relevant set: MW, heavy atom count,
        stereocenters, LogP, and synthetic accessibility score.
        """
        prop_df = PropertyGrabber.featurize_many(
            molecules=df["smiles"].to_list(),
            properties=properties,
            parallel=True,
            dataframe_format="polars",
        )
        return polars.concat([df, prop_df], how="horizontal")

    @update_table()
    def add_method_columns(
        cls,
        df: polars.DataFrame,
        method_map: dict = {"to_inchi_key": {}},
    ):
        """
        Computes method-based properties and adds them as columns.
        Defaults to InChI key only. Pass a custom method_map to extend,
        e.g. {"to_inchi_key": {}, "to_smiles": {}}.
        """
        method_df = MethodCaller.featurize_many(
            molecules=df["smiles"].to_list(),
            method_map=method_map,
            parallel=True,
            dataframe_format="polars",
        )
        return polars.concat([df, method_df], how="horizontal")

    @update_column("rule_of_5")
    def add_rule_of_5_column(cls, df: polars.DataFrame):
        """
        Computes Ro5 from physicochemical property columns (MW, LogP, HBA, HBD).
        Ro5 is True when: MW <= 500, LogP <= 5, HBA <= 10, HBD <= 5.
        These are the classic Lipinski cutoffs.
        Requires property columns to be present in the parquet.
        """
        return df.select(
            (
                (polars.col("molecular_weight_exact") <= 500)
                & (polars.col("log_p_rdkit") <= 5)
                & (polars.col("num_h_acceptors") <= 10)
                & (polars.col("num_h_donors") <= 5)
            ).alias("rule_of_5")
        )["rule_of_5"]

    # -------------------------------------------------------------------------

    # for datasets that require explicit-H smiles and fps

    @update_table()
    def convert_to_explicit_h_smiles(cls, df: polars.DataFrame):

        method_df = MethodCaller.featurize_many(
            molecules=df["smiles"].to_list(),
            method_map={_get_smiles_with_h: {}},
            parallel=True,
            dataframe_format="polars",
        )
        return df.with_columns(method_df.to_series(0).alias("smiles"))

    @update_table()
    def add_pattern_fingerprint_column(
        cls, df: polars.DataFrame, explicit_h: bool = False
    ):
        """
        Adds a base64-encoded PatternFingerprint column for substructure searches.
        Run after remove_invalid_smiles() to avoid errors on bad SMILES.
        """
        fingerprints = PatternFingerprint.featurize_many(
            molecules=df["smiles"].to_list(),
            parallel=True,
            vector_type="base64",
            explicit_h=explicit_h,
        )
        return df.with_columns(polars.Series("pattern_fingerprint", fingerprints))

    # -------------------------------------------------------------------------

    # for billion-scale fingerprint similarity searches

    index_engine: str = "usearch"
    """
    "usearch" | "faiss-ivfpq" — the ANN backend used to build and search indexes.

    - ``"usearch"``: HNSW graph over the packed bits with an exact Tanimoto
      metric. Exact distances, but the graph itself is large on disk.
    - ``"faiss-ivfpq"``: IVF coarse clustering + product quantization. Each
      vector compresses to ``faiss_settings["m"]`` bytes, so indexes are far
      smaller than HNSW, at the cost of approximate recall. Returned distances
      are still exact Tanimoto (candidates get reranked). Requires the optional
      ``faiss-cpu`` package.
    """

    index_batch_size: int = 1
    """
    chunk_key batches per index file; 1 = one file per chunk
    """

    index_load_mode: str = "memory"
    """
    "memory" | "view" | "scan" | "scan-zstd" — see load_fingerprint_index()

    Note that "view" is usearch-only; IVF+PQ indexes cannot be memory-mapped.
    """

    faiss_settings: dict = {
        # IVF clusters. Rule of thumb ~sqrt(total rows); training wants
        # >= 39 * nlist vectors. At billion scale this is ~1e5-1e6.
        "nlist": 4096,
        # PQ sub-quantizers. Must divide the fingerprint's ndim, and doubles as
        # the compressed bytes/vector at nbits=8 -- the main disk/RAM knob
        # (8 B/vector here vs. 128 B/vector stored raw).
        "m": 8,
        # Bits per PQ code -> 2^nbits entries per sub-quantizer codebook.
        "nbits": 8,
        # Clusters scanned per query. The primary recall vs. speed knob.
        "nprobe": 16,
    }
    """
    IVF+PQ tuning for the "faiss-ivfpq" engine. Ignored by the usearch engine.
    Override the whole dict on a subclass to tune.
    """

    _ENGINE_SUFFIXES = {"usearch": "usearch", "faiss-ivfpq": "faiss"}
    # engine -> index file extension, so both engines can coexist in vectors/

    _fingerprint_indexes: dict = {}
    # _cache_key() -> (mode, payload), cached after the first load

    _faiss_templates: dict = {}
    # (app, datastore, fp_type) -> trained-but-empty index, read once per process

    _FP_CONFIGS = {
        "maccs": {
            "ndim": 168,
            "stored_bytes": 21,
            "metric_fn": tanimoto_maccs,
            "featurizer": MaccsFingerprint,
        },
        "ecfp4": {
            "ndim": 2048,
            "stored_bytes": 256,
            "metric_fn": tanimoto_ecfp4,
            "featurizer": Ecfp4Fingerprint,
        },
        "fcfp4": {
            "ndim": 2048,
            "stored_bytes": 256,
            "metric_fn": tanimoto_ecfp4,  # same 2048-bit packed layout as ecfp4
            "featurizer": Fcfp4Fingerprint,
        },
        "ecfp4_1024": {
            "ndim": 1024,
            "stored_bytes": 128,
            "metric_fn": tanimoto_ecfp4_1024,
            "featurizer": Ecfp4Fingerprint,
            "featurizer_kwargs": {"size": 1024},
        },
        "fcfp4_1024": {
            "ndim": 1024,
            "stored_bytes": 128,
            "metric_fn": tanimoto_ecfp4_1024,
            "featurizer": Fcfp4Fingerprint,
            "featurizer_kwargs": {"size": 1024},
        },
    }

    @update_table()
    def add_fingerprints(
        cls,
        df: polars.DataFrame,
        fingerprint_type: str = "usearch",
    ):
        """
        Add fingerprint column(s) to each chunk parquet.

        Note:
            For bulk dataset builds, run after ``repartition("chunk_key")``
            and ``promote_staging()`` have completed.

        Args:
            fingerprint_type: Controls which fingerprint column(s) are added.

                - ``"usearch"`` (default): Adds three packed-bit binary columns
                  (``maccs``, ``ecfp4``, ``fcfp4``) computed together in one
                  pass via ``USearchFingerprints``.
                - ``"maccs"``, ``"ecfp4"``, or ``"fcfp4"``: Adds a single
                  packed-bit binary column with that name.

        Raises:
            ValueError: If ``fingerprint_type`` is not recognized.
        """
        if fingerprint_type == "usearch":
            if len(df) == 0:
                return df.with_columns(
                    polars.Series("maccs", [], dtype=polars.Binary),
                    polars.Series("ecfp4", [], dtype=polars.Binary),
                    polars.Series("fcfp4", [], dtype=polars.Binary),
                )
            fingerprints = USearchFingerprints.featurize_many(
                df["smiles"].to_list(), parallel=True
            )
            maccs_list, ecfp4_list, fcfp4_list = zip(*fingerprints)
            return df.with_columns(
                polars.Series("maccs", list(maccs_list)),
                polars.Series("ecfp4", list(ecfp4_list)),
                polars.Series("fcfp4", list(fcfp4_list)),
            )

        elif fingerprint_type in cls._FP_CONFIGS:
            if len(df) == 0:
                return df.with_columns(
                    polars.Series(fingerprint_type, [], dtype=polars.Binary)
                )
            cfg = cls._FP_CONFIGS[fingerprint_type]
            fp_list = cfg["featurizer"].featurize_many(
                df["smiles"].to_list(),
                parallel=True,
                vector_type="numpy_packbits_bytes",
                **cfg.get("featurizer_kwargs", {}),
            )
            return df.with_columns(polars.Series(fingerprint_type, fp_list))

        else:
            valid = ["usearch"] + list(cls._FP_CONFIGS.keys())
            raise ValueError(
                f"Unknown fingerprint_type {fingerprint_type!r}. Valid options: {valid}"
            )

    # -- shared helpers (both engines) --

    @classmethod
    def _index_suffix(cls) -> str:
        """
        File extension used by the active index engine, so usearch and faiss
        indexes can live side by side in the vectors/ directory.
        """
        if cls.index_engine not in cls._ENGINE_SUFFIXES:
            raise ValueError(
                f"Unknown index_engine: {cls.index_engine!r}. "
                f"Use one of {list(cls._ENGINE_SUFFIXES.keys())}."
            )
        return cls._ENGINE_SUFFIXES[cls.index_engine]

    @classmethod
    @property
    def vectors_directory(cls) -> Path:
        """Directory holding the fingerprint index shards."""
        return get_directory(cls.base_directory / "vectors")

    @classmethod
    def _use_zstd(cls) -> bool:
        """Whether shards are written zstd-compressed."""
        return cls.index_load_mode == "scan-zstd"

    @classmethod
    def _shard_paths(cls, fp_type: str, batch: list[int]) -> tuple[Path, Path]:
        """
        The ``(uncompressed, final)`` shard paths for one batch of chunk_keys.
        The two differ only when compression is on, where the final file gains a
        ``.zst`` suffix.
        """
        uncompressed = cls.vectors_directory / cls._shard_name(fp_type, batch)
        if not cls._use_zstd():
            return uncompressed, uncompressed
        return uncompressed, cls._add_suffix(uncompressed, ".zst")

    @classmethod
    def _shard_name(cls, fp_type: str, batch: list[int]) -> str:
        """Filename of one batch's uncompressed shard."""
        return f"{fp_type}-{batch[0]}-{batch[-1]}.{cls._index_suffix()}"

    @staticmethod
    def _add_suffix(path: Path, suffix: str) -> Path:
        """Appends a suffix rather than replacing the existing one."""
        return path.with_suffix(path.suffix + suffix)

    @classmethod
    def _built_shard_names(cls, fp_type: str) -> set[str]:
        """
        Names of every shard already on disk, for resume checks.

        One directory listing rather than a stat per batch -- a full build asks
        about tens of thousands of batches, and the datastore directory is often
        network-backed.
        """
        return {p.name for p in cls.vectors_directory.glob(f"{fp_type}-*")}

    @classmethod
    def _shard_exists(cls, fp_type: str, batch: list[int]) -> bool:
        """
        Whether a batch's shard is already built. Either compression counts, so
        that flipping index_load_mode does not trigger a full rebuild.
        """
        name = cls._shard_name(fp_type, batch)
        built = cls._built_shard_names(fp_type)
        return name in built or f"{name}.zst" in built

    @classmethod
    def _index_files(cls, fp_type: str) -> list[Path]:
        """
        Sorted index shard files for the active engine.

        The ``{fp_type}-*`` prefix excludes the faiss training template
        (``{fp_type}.template.faiss``), and ``.partial`` files left behind by an
        interrupted build are skipped so they are never searched.
        """
        pattern = f"{fp_type}-*.{cls._index_suffix()}*"
        return sorted(
            p
            for p in cls.vectors_directory.glob(pattern)
            if p.is_file() and p.suffix != ".partial"
        )

    @classmethod
    def _cache_key(cls, fp_type: str) -> tuple:
        """
        Cache key for ``_fingerprint_indexes``.

        Includes the app/datastore because ``_fingerprint_indexes`` is a mutable
        dict defined on ``MoleculeDatastore`` itself and is therefore shared by
        every subclass -- keying on fp_type alone would let two datastores
        collide on the same "ecfp4" entry. Engine and load mode are included so
        that changing either one re-loads instead of silently reusing a payload
        built under the old setting.
        """
        return (
            cls.app_name,
            cls.datastore_name,
            cls.index_engine,
            cls.index_load_mode,
            fp_type,
        )

    @classmethod
    def _chunk_fingerprints(cls, chunk_key: int, fp_type: str) -> polars.LazyFrame:
        """
        Lazy frame of just the id + fingerprint columns for one chunk_key.

        Scans the chunk's own parquet file(s) directly when the datastore is
        hive-partitioned by chunk_key. Filtering ``cls.lf`` instead would work,
        but re-resolves a glob over every partition in the datastore (20k+ dirs)
        on each collect -- and index builds collect one chunk many times over.
        """
        partition_dir = cls.live_directory / f"chunk_key={chunk_key}"
        if partition_dir.is_dir():
            lazy_df = polars.scan_parquet(partition_dir / "*.parquet")
        else:
            # Not partitioned by chunk_key (or partitioned some other way)
            lazy_df = cls.lf.filter(polars.col("chunk_key") == chunk_key)
        return lazy_df.select("datastore_id", fp_type)

    @classmethod
    def _packed_fingerprints(cls, df: polars.DataFrame, fp_type: str) -> numpy.ndarray:
        """
        Converts a fingerprint column of packed bytes into a uint8
        (n_rows, stored_bytes) matrix.

        Casting to a fixed-width binary type makes the column's values one
        contiguous arrow buffer, so the matrix is a zero-copy view over it. This
        runs on every row of every chunk during a build, which is why it avoids
        a per-row python loop.
        """
        stored_bytes = cls._FP_CONFIGS[fp_type]["stored_bytes"]
        fps = (
            df.to_arrow()
            .column(fp_type)
            .cast(pyarrow.binary(stored_bytes))
            .combine_chunks()
        )
        values = numpy.frombuffer(fps.buffers()[1], dtype=numpy.uint8)
        # buffers() ignores the array's own offset, so re-apply it here
        start = fps.offset * stored_bytes
        return values[start : start + len(fps) * stored_bytes].reshape(-1, stored_bytes)

    @classmethod
    def _unpacked_fingerprints(
        cls, df: polars.DataFrame, fp_type: str
    ) -> numpy.ndarray:
        """
        Converts a fingerprint column of packed bytes into the float32
        (n_rows, ndim) matrix that faiss expects.
        """
        packed = cls._packed_fingerprints(df, fp_type)
        return numpy.unpackbits(packed, axis=1).astype(numpy.float32)

    @staticmethod
    def _hits_dataframe(datastore_ids, distances, count: int) -> polars.DataFrame:
        """
        The shared return shape of every search method: top-k hits sorted by
        ascending distance.
        """
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

        Popcounts the packed bytes directly rather than unpacking to bits, which
        matches what the numba metrics in ``numba_funcs`` compute.
        """
        intersection = numpy.bitwise_count(query & candidates).sum(axis=1)
        union = numpy.bitwise_count(query | candidates).sum(axis=1)
        # Guard the empty-fingerprint case (union == 0 means both are all-zero)
        with numpy.errstate(invalid="ignore", divide="ignore"):
            similarity = numpy.where(union > 0, intersection / union, 0.0)
        return (1 - similarity).astype(numpy.float32)

    # -------------------------------------------------------------------------

    # building indexes

    @classmethod
    def build_fingerprint_index(
        cls,
        fp_type: str = "ecfp4",
        parallel_job: bool = False,
    ) -> None:
        """
        Builds similarity search indexes from the chunk parquet files.

        Creates one index file per batch of chunk_keys (sized by index_batch_size)
        and writes them to datastore_dir/vectors/. Run after add_fingerprints()
        has fully completed.

        The ``index_engine`` attribute selects the backend ("usearch" or
        "faiss-ivfpq"). For faiss, a shared IVF+PQ template is trained once up
        front (see ``train_faiss_template``) and reused by every batch so all
        shards share centroids and codebooks.
        """
        chunk_keys = list(range(cls.num_chunks))
        batches = [list(b) for b in chunk_list(chunk_keys, cls.index_batch_size)]
        # One listing shared by every batch, instead of a stat per batch
        built = cls._built_shard_names(fp_type)
        batches_to_process = [
            b
            for b in batches
            if cls._shard_name(fp_type, b) not in built
            and f"{cls._shard_name(fp_type, b)}.zst" not in built
        ]
        logging.info(
            f"{len(batches) - len(batches_to_process)} batches already done, "
            f"{len(batches_to_process)} to process"
        )

        # Train before dispatching so that parallel workers all reuse one template
        if cls.index_engine == "faiss-ivfpq" and batches_to_process:
            cls.train_faiss_template(fp_type)

        dispatch(
            batches_to_process,
            cls._build_fingerprint_index_single_batch,
            parallel="job" if parallel_job else "single",
            fp_type=fp_type,
        )
        logging.info(f"{cls.index_engine} index build complete!")

    @classmethod
    def _build_fingerprint_index_single_batch(
        cls,
        batch: list[int],
        fp_type: str = "ecfp4",
    ):
        uncompressed_path, index_path = cls._shard_paths(fp_type, batch)
        logging.info(f"Building {fp_type} batch {batch[0]}-{batch[-1]} → {index_path}")
        builder = (
            cls._build_faiss_batch
            if cls.index_engine == "faiss-ivfpq"
            else cls._build_usearch_batch
        )
        builder(batch, fp_type, uncompressed_path, index_path)

    @classmethod
    def _build_usearch_batch(
        cls,
        batch: list[int],
        fp_type: str,
        uncompressed_path: Path,
        index_path: Path,
    ):
        """
        Builds one usearch HNSW shard, saving after each chunk so an interrupted
        build can resume mid-batch.
        """
        cfg = cls._FP_CONFIGS[fp_type]
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
            logging.info(f"  {fp_type} chunk_key={chunk_key}")
            df = cls._chunk_fingerprints(chunk_key, fp_type).collect()
            if len(df) == 0:
                continue

            keys = df["datastore_id"].to_numpy()
            if len(index) > 0 and keys[0] in index:
                logging.info(f"  Skipping chunk_key={chunk_key} - already indexed.")
                continue

            index.add(keys, cls._packed_fingerprints(df, fp_type))
            index.save(str(uncompressed_path))

            if cls._use_zstd():
                compressed = zstd.ZstdCompressor().compress(
                    uncompressed_path.read_bytes()
                )
                index_path.write_bytes(compressed)

            logging.info(f"  Saved progress | Vectors: {len(index):,}")

        if cls._use_zstd():
            uncompressed_path.unlink(missing_ok=True)

    @classmethod
    def _build_faiss_batch(
        cls,
        batch: list[int],
        fp_type: str,
        uncompressed_path: Path,
        index_path: Path,
    ):
        """
        Builds one IVF+PQ shard from the shared training template.
        """
        faiss = _get_faiss()

        # Clone the template rather than re-reading it: it is trained but empty,
        # so each shard gets its own index sharing the centroids/codebooks. The
        # centroids alone are ~17-34 MB, and a full build has thousands of batches.
        index = faiss.clone_index(cls._faiss_template(fp_type))

        # Rows unpacked to float32 at a time. Caps peak RAM: a 250k x 1024 slice
        # is ~1 GB, while unpacking a full 4M-row chunk at once would be ~16 GB.
        add_batch_size = 250_000

        for chunk_key in batch:
            logging.info(f"  {fp_type} chunk_key={chunk_key}")
            lazy_df = cls._chunk_fingerprints(chunk_key, fp_type)
            offset = 0
            while True:
                df = lazy_df.slice(offset, add_batch_size).collect()
                if len(df) == 0:
                    break
                index.add_with_ids(
                    cls._unpacked_fingerprints(df, fp_type),
                    df["datastore_id"].to_numpy().astype(numpy.int64),
                )
                offset += len(df)
            logging.info(f"  Added {offset:,} | Vectors: {index.ntotal:,}")

        # Write to a temp path and rename, so an interrupted build never leaves
        # a partial file that the resume check would mistake for a finished one.
        # (usearch saves incrementally instead; IVF+PQ has no partial-save path.)
        temp_path = cls._add_suffix(uncompressed_path, ".partial")
        if cls._use_zstd():
            raw = faiss.serialize_index(index).tobytes()
            temp_path.write_bytes(zstd.ZstdCompressor().compress(raw))
        else:
            faiss.write_index(index, str(temp_path))
        temp_path.replace(index_path)
        logging.info(f"  Saved {index.ntotal:,} vectors → {index_path}")

    @classmethod
    def _faiss_template_file(cls, fp_type: str) -> Path:
        """
        Path of the trained-but-empty IVF+PQ index shared by all shards.

        Named ``<fp_type>.template.faiss`` so it never matches the
        ``<fp_type>-*.faiss*`` shard glob.
        """
        return cls.vectors_directory / f"{fp_type}.template.faiss"

    @classmethod
    def _faiss_template(cls, fp_type: str):
        """
        The trained-but-empty template index, read from disk once per process.
        """
        cache_key = (cls.app_name, cls.datastore_name, fp_type)
        if cache_key not in cls._faiss_templates:
            path = cls._faiss_template_file(fp_type)
            cls._faiss_templates[cache_key] = _get_faiss().read_index(str(path))
        return cls._faiss_templates[cache_key]

    @classmethod
    def train_faiss_template(cls, fp_type: str = "ecfp4", rebuild: bool = False):
        """
        Trains the IVF centroids and PQ codebooks on a sample of the datastore
        and saves the empty result as a template.

        Every shard is built from this one template, which is what makes the
        shards mutually comparable: distances only mean the same thing across
        shards when they share centroids and codebooks. Training is the only
        step that needs a broad view of the data, so it happens once here rather
        than per batch.

        Args:
            fp_type: Fingerprint type to train for.
            rebuild: Retrain and overwrite an existing template. Note that any
                shards already built from the old template become invalid.
        """
        faiss = _get_faiss()

        template_file = cls._faiss_template_file(fp_type)
        if template_file.exists() and not rebuild:
            return template_file

        nlist, m, nbits = (cls.faiss_settings[k] for k in ["nlist", "m", "nbits"])
        ndim = cls._FP_CONFIGS[fp_type]["ndim"]
        if ndim % m != 0:
            raise ValueError(
                f"faiss_settings['m'] ({m}) must divide the {fp_type} ndim ({ndim})."
            )

        vectors = cls._sample_training_vectors(fp_type)
        if len(vectors) < 39 * nlist:
            logging.warning(
                f"Only {len(vectors):,} training vectors for nlist={nlist} "
                f"(faiss wants >= {39 * nlist:,}). Lower nlist in faiss_settings."
            )

        logging.info(
            f"Training {fp_type} IVF+PQ on {len(vectors):,} vectors | "
            f"nlist={nlist}, m={m}, nbits={nbits}"
        )
        index = faiss.IndexIVFPQ(faiss.IndexFlatL2(ndim), ndim, nlist, m, nbits)
        index.train(vectors)

        faiss.write_index(index, str(template_file))
        # Drop any stale copy cached from a previous template
        cls._faiss_templates.pop((cls.app_name, cls.datastore_name, fp_type), None)
        logging.info(f"Saved training template → {template_file}")
        return template_file

    @classmethod
    def _sample_training_vectors(cls, fp_type: str) -> numpy.ndarray:
        """
        Samples ~250k fingerprints spread across the datastore for training.

        Reads a slice from each of up to 64 evenly spaced chunk files. Sampling
        across chunks matters because chunk_key groups related molecules, so the
        first chunk alone is not representative of the whole space.
        """
        train_size = 250_000
        max_files = 64

        chunk_files = cls.chunk_files
        if not chunk_files:
            raise FileNotFoundError(
                f"No parquet files found in {cls.live_directory}. "
                "Nothing to train an index on."
            )

        if len(chunk_files) > max_files:
            step = len(chunk_files) / max_files
            chunk_files = [chunk_files[int(i * step)] for i in range(max_files)]

        rows_per_file = max(1, train_size // len(chunk_files))
        frames = []
        for file in chunk_files:
            df = polars.read_parquet(file, columns=[fp_type], n_rows=rows_per_file)
            if len(df) > 0:
                frames.append(df)

        return cls._unpacked_fingerprints(polars.concat(frames), fp_type)

    # -------------------------------------------------------------------------

    # loading + searching indexes

    @classmethod
    def load_fingerprint_index(cls, fp_type: str = "ecfp4") -> None:
        """
        Loads index files and caches them under ``_fingerprint_indexes``.

        Behavior is controlled by ``index_load_mode``:

        - ``"memory"``: Load all index files into RAM (fastest search, highest RAM).
        - ``"view"``: Open all files as a single memory-mapped ``Indexes`` object
          (low RAM, nearly as fast as memory mode). USearch only.
        - ``"scan"``: Store file paths only; ``search_similar`` opens each file
          one at a time (lowest RAM, slowest search).
        - ``"scan-zstd"``: Like scan, but reads zstd compressed index files.

        Args:
            fp_type: Fingerprint type to load. One of ``"ecfp4"``, ``"maccs"``,
                ``"fcfp4"``, ``"ecfp4_1024"``, or ``"fcfp4_1024"``.
        """
        cache_key = cls._cache_key(fp_type)
        if cache_key in cls._fingerprint_indexes:
            return

        mode = cls.index_load_mode
        is_faiss = cls.index_engine == "faiss-ivfpq"
        if mode not in ["memory", "view", "scan", "scan-zstd"]:
            raise ValueError(
                f"Unknown index_load_mode: {mode!r}. "
                "Use 'memory', 'view', 'scan', or 'scan-zstd'."
            )
        if mode == "view" and is_faiss:
            # IVF+PQ indexes cannot be memory-mapped, so "view" has no faiss
            # equivalent. Scan mode uses IO_FLAG_READ_ONLY as the closest analog.
            raise ValueError(
                "index_load_mode='view' is not supported by the faiss-ivfpq "
                "engine (IVF+PQ indexes cannot be memory-mapped). "
                "Use 'memory', 'scan', or 'scan-zstd'."
            )

        index_files = cls._index_files(fp_type)
        if not index_files:
            raise FileNotFoundError(
                f"No {fp_type} {cls.index_engine} index files found in "
                f"{cls.base_directory / 'vectors'}. "
                "Run build_fingerprint_index() first."
            )

        n_files = f"{len(index_files)} {fp_type} {cls.index_engine} index file(s)"
        if mode == "memory":
            logging.info(f"Loading {n_files} into RAM...")
            payload = [cls._read_index(p, into_memory=True) for p in index_files]
            n_vectors = sum(i.ntotal if is_faiss else len(i) for i in payload)
            logging.info(f"Loaded {n_vectors:,} vectors.")
        elif mode == "view":
            logging.info(f"Opening {n_files} as memory-mapped views...")
            payload = Indexes(paths=[str(p) for p in index_files], view=True)
        else:  # scan / scan-zstd -- opened one at a time at search time
            logging.info(f"Registering {n_files} for scan-mode search.")
            payload = index_files

        cls._fingerprint_indexes[cache_key] = (mode, payload)

    @classmethod
    def _read_index(cls, path: Path, into_memory: bool = False):
        """
        Reads a single index shard for the active engine, transparently handling
        zstd-compressed files.

        Args:
            path: Index shard to read.
            into_memory: Fully load into RAM. Only affects uncompressed usearch
                shards, which are otherwise opened as a memory-mapped view.
                Compressed shards must always be decompressed into RAM, and
                IVF+PQ shards cannot be mapped at all.
        """
        is_zstd = path.suffix == ".zst"
        raw = (
            zstd.ZstdDecompressor().decompress(path.read_bytes()) if is_zstd else None
        )

        if cls.index_engine != "faiss-ivfpq":
            if is_zstd:
                return Index.restore(raw)
            if into_memory:
                return Index.restore(str(path))
            return Indexes(paths=[str(path)], view=True)

        faiss = _get_faiss()

        index = (
            faiss.deserialize_index(numpy.frombuffer(raw, dtype=numpy.uint8))
            if is_zstd
            else faiss.read_index(str(path), faiss.IO_FLAG_READ_ONLY)
        )
        index.nprobe = cls.faiss_settings["nprobe"]
        return index

    @classmethod
    def _iter_indexes(cls, mode: str, payload):
        """
        Yields every shard to search. Under "memory" the shards are already
        loaded, so this just hands them back; under the scan modes they are
        opened lazily, one at a time, to keep only one in RAM.
        """
        if mode == "memory":
            return payload
        return (cls._read_index(path) for path in payload)

    @classmethod
    def search_similar(
        cls,
        query,
        count: int = 50,
        fp_type: str = "ecfp4",
    ) -> "polars.DataFrame":
        """
        Searches the fingerprint indexes for molecules similar to the query.

        Uses the cached index loaded by ``load_fingerprint_index()``, calling it
        automatically on first use. Search behavior depends on ``index_engine``
        and ``index_load_mode``.

        Args:
            query: Query molecule as a ``Molecule`` object or SMILES string.
            count: Number of top results to return.
            fp_type: Fingerprint type to use. One of ``"ecfp4"``, ``"maccs"``,
                ``"fcfp4"``, ``"ecfp4_1024"``, or ``"fcfp4_1024"``.

        Returns:
            polars.DataFrame with columns ``datastore_id`` (Int64) and
            ``distance`` (Float32), sorted ascending by distance. Distances are
            Tanimoto for both engines (see ``_search_faiss``).
        """
        if isinstance(query, str):
            query = Molecule.from_smiles(query)

        cfg = cls._FP_CONFIGS[fp_type]
        fp_bytes = cfg["featurizer"].featurize(
            query,
            vector_type="numpy_packbits_bytes",
            **cfg.get("featurizer_kwargs", {}),
        )
        vec = numpy.frombuffer(fp_bytes, dtype=numpy.uint8).copy()

        cls.load_fingerprint_index(fp_type)  # no-op once cached
        mode, payload = cls._fingerprint_indexes[cls._cache_key(fp_type)]

        if cls.index_engine == "faiss-ivfpq":
            return cls._search_faiss(vec, count, fp_type, mode, payload)

        if mode == "view":
            # a single Indexes object spanning every shard
            matches = payload.search(vec, count)
            keys, distances = matches.keys.tolist(), matches.distances.tolist()
            return cls._hits_dataframe(keys, distances, count)

        all_keys, all_distances = [], []
        for index in cls._iter_indexes(mode, payload):
            matches = index.search(vec, count)
            all_keys.extend(matches.keys.tolist())
            all_distances.extend(matches.distances.tolist())
        return cls._hits_dataframe(all_keys, all_distances, count)

    @classmethod
    def _search_faiss(
        cls,
        vec: numpy.ndarray,
        count: int,
        fp_type: str,
        mode: str,
        payload: list,
    ) -> "polars.DataFrame":
        """
        Searches IVF+PQ shards and reranks the candidates by exact Tanimoto.

        IVF+PQ returns L2 distances between *quantized* vectors, which are both
        lossy and on a different scale than the usearch engine's Tanimoto. So the
        raw hits are treated as candidates only: this oversamples them, re-reads
        their true fingerprints from the parquets, and scores those exactly. That
        keeps ``search_similar`` returning real Tanimoto distances regardless of
        which engine built the index.
        """
        # Oversample so that reranking has room to reorder into the true top-k
        n_candidates = count * 4
        query_vector = numpy.unpackbits(vec).astype(numpy.float32)[None, :]

        # Each shard returns its own n_candidates, so keep the PQ distances and
        # narrow to a *global* n_candidates before touching any parquet. Without
        # this, a 2500-shard datastore would rerank 500k candidates spread over
        # every chunk file -- pruning nothing and reading the whole datastore.
        keys, pq_distances = [], []
        for index in cls._iter_indexes(mode, payload):
            shard_distances, shard_keys = index.search(query_vector, n_candidates)
            keys.append(shard_keys[0])
            pq_distances.append(shard_distances[0])

        keys = numpy.concatenate(keys)
        pq_distances = numpy.concatenate(pq_distances)

        # faiss pads with -1 when a shard holds fewer vectors than requested
        found = keys != -1
        keys, pq_distances = keys[found], pq_distances[found]
        if len(keys) == 0:
            return cls._hits_dataframe([], [], count)

        if len(keys) > n_candidates:
            closest = numpy.argpartition(pq_distances, n_candidates)[:n_candidates]
            keys = keys[closest]

        candidate_ids = numpy.unique(keys)
        df = (
            cls.filter(datastore_id__in=candidate_ids.tolist())
            .select("datastore_id", fp_type)
            .collect()
        )
        return cls._hits_dataframe(
            df["datastore_id"].to_numpy().astype(numpy.int64),
            cls._tanimoto_distances(vec, cls._packed_fingerprints(df, fp_type)),
            count,
        )


def _get_faiss():
    """
    Imports faiss, which is an optional dependency of the "faiss-ivfpq" engine.
    """
    try:
        import faiss
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "You must have faiss installed to use the 'faiss-ivfpq' index engine. "
            "Install it with 'pip install simmate[faiss]'"
        )
    return faiss


# top-level (not a method) so it is picklable for multiprocessing
def _get_smiles_with_h(molecule):
    """Return SMILES with explicit hydrogens added."""
    molecule.add_hydrogens()
    return molecule.to_smiles()
