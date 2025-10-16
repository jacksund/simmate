# -*- coding: utf-8 -*-

import logging
from functools import cached_property

import polars
from rdkit.Chem import rdSubstructLibrary
from rich.progress import track

from simmate.toolkit import Molecule
from simmate.utilities import filter_polars_df

from ..featurizers import PatternFingerprint
from ..featurizers.utilities import load_rdkit_fingerprint_from_base64
from ..filters import AllowedElements


class MoleculeDataFrame:
    """
    This helper class that manages a normal polars dataframe, but it has a
    couple of helpful methods added for loading molecules as well as
    running substructure and similarity searches.

    This class is helpful when you have a large dataset (>1 million) that you
    will be performing many operations/queries on and have plenty of RAM to
    keep fingerprints and/or molecule objects stored in RAM with it.

    Lazy queries are not supported
    """

    # TODO: add check to ensure user has enough RAM
    # For the smiles strs alone, you need ~1.5gb per 10mil molecules
    # For the substruct lib, you need ~4.5gb per 10mil molecules
    # For the morgan fp lib, you need ___gb per 10mil molecules

    def __init__(
        self,
        df: polars.DataFrame,
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
        parallel: bool = False,
    ):

        if all([c not in df.columns for c in ["smiles", "molecule", "molecule_obj"]]):
            raise Exception(
                "The dataframe must have a `smiles`, `molecule`, or `molecule_obj` column "
                "in order to generate a full dataframe."
            )

        self.df = df
        self.parallel = parallel
        if init_toolkit_objs and "molecule_obj" not in df.columns:
            self.init_toolkit_objs()
        if init_substructure_lib:
            self.init_substructure_lib()
        if init_morgan_fp_lib:
            self.init_morgan_fp_lib()

    # init methods are kept separate to keep code organized and also allow cols
    # to be populated dynamically at a later time

    def init_toolkit_objs(self):
        # priority of columns goes..
        # 1. molecule_obj (ie nothing to do)
        # 2. molecule (use from_dynamic)
        # 3. smiles (use from_smiles)
        logging.info("Building `toolkit.Molecule` objects...")

        if "molecule_obj" in self.df.columns:
            pass  # nothing to do

        elif "molecule" in self.df.columns:
            mol_objs = [Molecule.from_dynamic(m) for m in track(self.df["molecule"])]
            self.df = self.df.with_columns(polars.Series("molecule_obj", mol_objs))

        elif "smiles" in self.df.columns:
            mol_objs = [Molecule.from_smiles(m) for m in track(self.df["smiles"])]
            self.df = self.df.with_columns(polars.Series("molecule_obj", mol_objs))

    def init_substructure_lib(self):
        logging.info(
            "Building `pattern_fingerprint` column for substructure searches..."
        )
        mol_col = self._get_molecule_column()

        if "pattern_fingerprint" not in self.df.columns:
            fingerprints = PatternFingerprint.featurize_many(
                molecules=self.df[mol_col],
                parallel=self.parallel,
                vector_type="rdkit",
            )
            self.df = self.df.with_columns(
                polars.Series("pattern_fingerprint", fingerprints)
            )

        elif isinstance(self.df["pattern_fingerprint"][0], str):
            # assume we have a base64 str of the fingerprint
            fingerprints = [
                load_rdkit_fingerprint_from_base64(fp)
                for fp in track(self.df["pattern_fingerprint"])
            ]
            self.df = self.df.with_columns(
                polars.Series("pattern_fingerprint", fingerprints)
            )
        else:
            pass  # assume pattern_fingerprint col is already in correct format

    def init_morgan_fp_lib(self):
        raise NotImplementedError("")  # TODO
        # logging.info(
        #     "Building `morgan_fingerprint` column for 2D similarity searches..."
        # )
        # mol_col = self._get_molecule_column()
        # if "morgan_fingerprint" not in self.df.columns:
        #     pass
        # elif isinstance(self.df["morgan_fingerprint"][0], str):
        #     pass
        # else:
        #     pass

    def _get_molecule_column(self):
        priority_order = ["molecule_obj", "molecule", "smiles"]
        for col_name in priority_order:
            if col_name in self.df.columns:
                return col_name
        raise ValueError(
            f"DataFrame does not contain any of the accepted molecule columns: {priority_order}"
        )

    # -------------------------------------------------------------------------

    def filter(
        self,
        limit: int = None,
        # django-like filters for columns (e.g. id__lte=100)
        **kwargs,
    ):
        if not kwargs:
            raise Exception("No filter conditions given.")

        filtered_df = filter_polars_df(self.df, **kwargs)

        if limit:
            filtered_df = filtered_df.limit(limit)

        return MoleculeDataFrame.from_polars(filtered_df)

    # -------------------------------------------------------------------------

    @classmethod
    def from_parquet(cls, filename: str, **kwargs):
        return cls(polars.read_parquet(filename), **kwargs)

    @classmethod
    def from_csv(cls, filename: str, **kwargs):
        return cls(polars.read_csv(filename), **kwargs)

    @classmethod
    def from_polars(cls, df: polars.DataFrame, **kwargs):
        return cls(df, **kwargs)

    # @classmethod
    # def from_pandas(cls, df: pandas.DataFrame, **kwargs):
    #     return cls(polars.from_pandas(df), **kwargs)

    # -------------------------------------------------------------------------

    # Note! This section is *extremely* similar to the MoleculeSearchResults
    # methods for the django-based implementation for postgres-rdkit. There
    # are small differences because here we have all molecules loaded into
    # memory as a polars df, rather than having things on disk in a postgres db

    def filter_molecule_exact(self, molecule: Molecule):
        molecule = Molecule.from_dynamic(molecule)
        return self.filter(inchi_key=molecule.to_inchi_key())

    def filter_molecule_list_exact(self, molecules: list[Molecule] | str):
        if isinstance(molecules, str):
            # assume and try SMILES
            molecules = [Molecule.from_smiles(m) for m in molecules.split(".")]
        inchi_keys = [m.to_inchi_key() for m in molecules]
        return self.filter(inchi_key__in=inchi_keys)

    def filter_substructure(
        self,
        molecule_query: Molecule,
        limit: int = 20_000_000,
        nthreads: int = -1,
    ):

        # NOTE: it is much faster for us to use the underlying `substructure_library`
        # than it is to use a filter from the `toolkit.filters` module
        molecule_query = Molecule.from_dynamic(molecule_query)

        filtered_ids = self.substructure_library.GetMatches(
            molecule_query.rdkit_molecule,
            numThreads=nthreads,
            maxResults=limit,  # BUG: rdkit has no way to allow unlimited
        )
        filtered_ids = list(filtered_ids)

        return self.filter_from_ids(filtered_ids)

    def filter_similarity_2d(
        self,
        molecule: Molecule,
        cutoff: float = 0.5,
        order: bool = True,
    ):
        molecule = Molecule.from_dynamic(molecule)
        raise NotImplementedError("")  # TODO

    def filter_allowed_elements(self, elements: list[str]):
        mol_col = self._get_molecule_column()
        filtered_ids = AllowedElements.filter(
            molecules=self.df[mol_col],
            parallel=self.parallel,
            return_mode="index",
        )
        return self.filter_from_ids(filtered_ids)

    def filter_from_ids(self, ids: list[int]):
        # normally, we could just do something like...
        #   hits = [df[i] for i in hit_ids]
        # but polars api is messy, so we do this:
        filtered_df = (
            self.df.with_row_index("row_index")  # Add a temporary row_index column
            .filter(polars.col("row_index").is_in(ids))  # Filter using the list
            .drop("row_index")  # Drop the temporary index column
        )
        return self.__class__(filtered_df)

    # -------------------------------------------------------------------------

    @cached_property
    def substructure_library(self):
        logging.info("Generating substructure library...")
        if (
            "smiles" not in self.df.columns
            or "pattern_fingerprint" not in self.df.columns
        ):
            raise Exception(
                "The dataframe must have both `smiles` and `pattern_fingerprint` "
                "columns in order to generate a substructure library."
            )

        molecule_library = rdSubstructLibrary.CachedTrustedSmilesMolHolder()
        [molecule_library.AddSmiles(r) for r in self.df["smiles"]]

        # load_rdkit_fingerprint_from_base64 if instance base64 str
        fingerprint_library = rdSubstructLibrary.PatternHolder()
        [fingerprint_library.AddFingerprint(r) for r in self.df["pattern_fingerprint"]]

        library = rdSubstructLibrary.SubstructLibrary(
            molecule_library,
            fingerprint_library,
        )
        logging.info("Done")

        return library

    # -------------------------------------------------------------------------
