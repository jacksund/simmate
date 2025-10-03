# -*- coding: utf-8 -*-

import logging
from functools import cached_property
from pathlib import Path

import polars
from rdkit.Chem import rdSubstructLibrary

from simmate.toolkit import Molecule
from simmate.utilities import chunk_list, filter_polars_df, get_directory

from ..featurizers import (
    MethodCaller,
    MorganFingerprint,
    PatternFingerprint,
    PropertyGrabber,
)
from ..featurizers.utilities import load_rdkit_fingerprint_from_base64


class MoleculeDataFrame:
    """
    This helper class that manages a normal polars dataframe, but it has a
    couple of helpful methods added for loading molecules as well as
    running substructure and similarity searches.

    This class is helpful when you have a large dataset (>1 million) that you
    will be performing many operations/queries on and have plenty of RAM to
    keep fingerprints and/or molecule objects stored in RAM with it.

    The polars lazy queries are not yet supported
    """

    def __init__(
        self,
        df: polars.DataFrame,
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
    ):

        if any([c not in df.columns for c in ["smiles", "molecule", "molecule_obj"]]):
            raise Exception(
                "The dataframe must have a `smiles`, `molecule`, or `molecule_obj` column "
                "in order to generate a full dataframe."
            )

        self.df = df

        if init_toolkit_objs and "molecule_obj" not in self.df.columns:
            pass

        if init_substructure_lib:

            if "pattern_fingerprint" not in self.df.columns:
                pass
            elif isinstance(self.df["pattern_fingerprint"][0], str):
                pass
            else:
                pass

        if init_morgan_fp_lib:
            if "morgan_fingerprint" not in self.df.columns:
                pass
            elif isinstance(self.df["morgan_fingerprint"][0], str):
                pass
            else:
                pass

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
        limit: int = None,
        nthreads: int = -1,
    ):
        molecule_query = Molecule.from_dynamic(molecule_query)
        hit_ids = self.substructure_library.GetMatches(
            molecule_query.rdkit_molecule,
            maxResults=None,
            numThreads=nthreads,
        )
        hit_ids = list(hit_ids)

        # hits = [df[i] for i in hit_ids]
        filtered_df = (
            self.with_row_index("row_index")  # Add a temporary row_index column
            .filter(polars.col("row_index").is_in(hit_ids))  # Filter using the list
            .drop("row_index")  # Drop the temporary index column
        )
        return filtered_df

    def filter_similarity_2d(
        self,
        molecule: Molecule,
        cutoff: float = 0.5,
        order: bool = True,
    ):
        molecule = Molecule.from_dynamic(molecule)
        raise NotImplementedError("")  # TODO

    # -------------------------------------------------------------------------

    @cached_property
    def substructure_library(self):
        logging.info("Generating substructure library...")
        if "smiles" not in self.columns or "pattern_fingerprint" not in self.columns:
            raise Exception(
                "The dataframe must have both `smiles` and `pattern_fingerprint` "
                "columns in order to generate a substructure library."
            )

        molecule_library = rdSubstructLibrary.CachedTrustedSmilesMolHolder()
        _ = [molecule_library.AddSmiles(r[1]) for r in self["smiles"]]

        # load_rdkit_fingerprint_from_base64 if instance base64 str
        fingerprint_library = rdSubstructLibrary.PatternHolder()
        _ = [fingerprint_library.AddFingerprint(r) for r in self["pattern_fingerprint"]]

        library = rdSubstructLibrary.SubstructLibrary(
            molecule_library,
            fingerprint_library,
        )
        logging.info("Done")

        return library

    # -------------------------------------------------------------------------
