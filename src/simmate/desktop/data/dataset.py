from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import polars
from rdkit import Chem, RDLogger
from rdkit.Chem import rdSubstructLibrary

from simmate.desktop.data.columns import DataColumns
from simmate.desktop.data.readers import read_table
from simmate.toolkit import Molecule


class ToolkitDataset:
    """
    One table opened in the Toolkit tab: the dataframe, what its columns hold (see
    `DataColumns`), and its molecules when it has a column of SMILES.

    Molecules are made only when asked for (`molecule`), e.g. as a row's image is
    drawn, so even a large dataset opens quickly. Substructure searches need an index
    of every molecule, built once by `build_substructure_index` (slow, so run it in
    the background).
    """

    def __init__(self, df: polars.DataFrame, name: str = "Dataset"):
        self.name = name
        self.columns = DataColumns(df)
        self.df = self.columns.df  # e.g. with categoricals cast to strings
        self.molecule_column = self.columns.molecule_column
        self.height = self.df.height
        self._smiles = (
            self.df[self.molecule_column].to_list() if self.has_molecules else []
        )
        self._molecules: dict[int, Molecule | None] = {}
        self.substructure_library: rdSubstructLibrary.SubstructLibrary | None = None

    @classmethod
    def from_file(cls, path: Path) -> "ToolkitDataset":
        path = Path(path)
        return cls(read_table(path), name=path.stem)

    @staticmethod
    def count_rows(path: Path) -> int | None:
        """The number of rows in a parquet file, read from its metadata (fast), or
        None for other files."""
        path = Path(path)
        if path.suffix.lower() != ".parquet":
            return None
        return polars.scan_parquet(path).select(polars.len()).collect().item()

    @property
    def has_molecules(self) -> bool:
        return self.molecule_column is not None

    def add_columns(self, new: polars.DataFrame) -> tuple[list[str], list[str]]:
        """Add `new`'s columns (one value per row), replacing any of the same name.
        Returns the (added, replaced) column names."""
        added, replaced = self.columns.add_columns(new)
        self.df = self.columns.df
        return added, replaced

    # --- molecules ------------------------------------------------------------------------

    def smiles(self, row: int) -> str | None:
        return self._smiles[row] if self.has_molecules else None

    def molecule(self, row: int) -> Molecule | None:
        """The row's molecule, made on first use then cached. None when the row has
        no SMILES or it can't be read."""
        if row not in self._molecules:
            smiles = self.smiles(row)
            try:
                self._molecules[row] = Molecule.from_smiles(smiles) if smiles else None
            except Exception:
                self._molecules[row] = None
        return self._molecules[row]

    # --- substructure search --------------------------------------------------------------

    def build_substructure_index(self) -> Iterator[int]:
        """
        Builds the RDKit `SubstructLibrary` that `substructure_matches` searches, as
        in `MoleculeDataFrame.substructure_library`. Rows whose SMILES can't be read
        are indexed as empty molecules, so they never match but keep row numbers aligned.

        It's slow (~20s per 50k rows), so it's a generator: it yields the number of
        rows done after each one, letting a caller spread the work out (e.g. between
        UI events, see `IncrementalTask`). Exhaust it to build the whole index, e.g.
        `for _ in dataset.build_substructure_index(): pass`. The index is only set
        once every row is done.
        """
        molecules = rdSubstructLibrary.CachedTrustedSmilesMolHolder()
        fingerprints = rdSubstructLibrary.PatternHolder()
        for row, smiles in enumerate(self._smiles):
            # unreadable SMILES are expected, so their warnings are muted
            with _rdkit_quiet():
                rdkit_molecule = Chem.MolFromSmiles(smiles) if smiles else None
            if rdkit_molecule is None:
                smiles, rdkit_molecule = "", Chem.Mol()
            molecules.AddSmiles(smiles)
            fingerprints.AddFingerprint(Chem.PatternFingerprint(rdkit_molecule))
            yield row + 1
        self.substructure_library = rdSubstructLibrary.SubstructLibrary(
            molecules, fingerprints
        )

    def substructure_matches(self, query: Molecule) -> np.ndarray:
        """By row: True where the molecule contains `query`. Needs the index from
        `build_substructure_index`."""
        if self.substructure_library is None:
            raise RuntimeError("The substructure index hasn't been built yet")
        matches = np.zeros(self.height, dtype=bool)
        rows = self.substructure_library.GetMatches(
            query.rdkit_molecule,
            numThreads=-1,
            maxResults=max(self.height, 1),  # rdkit's default stops at 1000
        )
        matches[list(rows)] = True
        return matches


@contextmanager
def _rdkit_quiet():
    """Mute RDKit's logging within the block."""
    RDLogger.DisableLog("rdApp.*")
    try:
        yield
    finally:
        RDLogger.EnableLog("rdApp.*")
