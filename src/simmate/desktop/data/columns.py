import contextlib
import datetime
import warnings

import numpy as np
import polars
from rdkit import Chem, RDLogger

from simmate.toolkit import Structure

NUMBER = "number"
DATE = "date"
CATEGORY = "category"
TEXT = "text"
MOLECULE = "molecule"

# String columns with at most this many distinct values count as categories (e.g.
# a series or status); ones with more (IDs, names) are text.
MAX_CATEGORIES = 20

# Text columns longer than this on average (e.g. mol blocks or InChIs) are hidden
# from the table by default and left out of the search.
MAX_TEXT_LENGTH = 100

# How many values of a string column are tried as SMILES, and the share of them
# that must parse for it to count as the molecule column.
MOLECULE_SAMPLE = 50
MOLECULE_MIN_VALID = 0.9
# ...or this share, for a column named for SMILES (e.g. "smiles" or "canonical_smiles")
MOLECULE_MIN_VALID_NAMED = 0.5

# How many values of a `structure` column are tried as crystal structures (POSCAR
# or CIF text, as Simmate's database tables store them), and the share of them that
# must parse for it to count as the structure column.
STRUCTURE_SAMPLE = 5
STRUCTURE_MIN_VALID = 0.5

# Made by the app itself (e.g. by `MoleculeDataFrame`), never shown.
INTERNAL_COLUMNS = {"molecule_obj", "pattern_fingerprint"}

# Shown only when asked for (e.g. from the table's column chooser): values kept
# for reference rather than exploring, like a molecule as its source gave it
# before Simmate cleaned it up, its InChIKey, or whether it has 3D coordinates.
HIDDEN_COLUMNS = {"molecule_original", "inchi_key", "is_3d"}

DATE_FORMAT = "%Y-%m-%d"
SECONDS_PER_DAY = 86_400


class DataColumns:
    """What each of a dataframe's columns holds, and its values ready to plot.

    Every column gets a kind, worked out from its values rather than a fixed list:

    - `NUMBER`: ints and floats.
    - `DATE`: dates and datetimes, or strings that are all ISO dates (e.g. "2026-03-14").
    - `CATEGORY`: strings or booleans with at most `MAX_CATEGORIES` distinct values.
    - `MOLECULE`: the one string column of SMILES, if any (see `_find_molecule_column`).
    - `TEXT`: any other string column (e.g. IDs and names).

    Other columns (lists, objects, all-null) get no kind. Values are cached per column,
    as plots and filters ask for them on every redraw.

    A column of crystal structures (see `_find_structure_column`) is also noted as
    `structure_column`, though it keeps its kind (long text) for now.

    Columns can be added later with `add_columns` (e.g. by the Featurize panel).
    """

    def __init__(self, df: polars.DataFrame):
        self.df = df
        self.kinds: dict[str, str] = {}
        self.long_text: set[str] = set()
        self._dates: dict[str, polars.Series] = {}  # parsed, for string date columns
        self._numbers: dict[str, np.ndarray] = {}
        self._codes: dict[str, tuple[np.ndarray, list[str]]] = {}
        self._labels: list | None = None
        self.molecule_column = self._find_molecule_column()
        self.structure_column = self._find_structure_column()
        for key in df.columns:
            self._profile(key)
        self.id_column = self._find_id_column()

    def add_columns(self, new: polars.DataFrame) -> tuple[list[str], list[str]]:
        """Add `new`'s columns, replacing any of the same name, and work out what
        each holds. Returns the (added, replaced) column names."""
        replaced = [key for key in new.columns if key in self.df.columns]
        added = [key for key in new.columns if key not in replaced]
        self.df = self.df.with_columns(new)
        for key in new.columns:
            # forget what a replaced column held
            for cache in (self.kinds, self._dates, self._numbers, self._codes):
                cache.pop(key, None)
            self.long_text.discard(key)
            self._profile(key)
        return added, replaced

    # --- column kinds ---------------------------------------------------------------------

    def _profile(self, key: str):
        """Work out column `key`'s kind, and whether it's long text."""
        dtype = self.df[key].dtype
        kind = MOLECULE if key == self.molecule_column else self._kind(key, dtype)
        if kind:
            self.kinds[key] = kind
        if (
            kind == TEXT
            and (self.df[key].str.len_chars().mean() or 0) > MAX_TEXT_LENGTH
        ):
            self.long_text.add(key)

    def _kind(self, key: str, dtype) -> str | None:
        if key in INTERNAL_COLUMNS:
            return None
        if dtype.is_numeric():
            return NUMBER
        if dtype in (polars.Date, polars.Datetime):
            return DATE
        if dtype == polars.Boolean:
            return CATEGORY
        if dtype in (polars.Categorical, polars.Enum):
            dtype = polars.String
            self.df = self.df.with_columns(polars.col(key).cast(polars.String))
        if dtype != polars.String:
            return None
        column = self.df[key]
        if column.null_count() == column.len():
            return None
        dates = column.str.to_date(DATE_FORMAT, strict=False)
        if dates.null_count() == column.null_count():
            self._dates[key] = dates
            return DATE
        if column.n_unique() <= MAX_CATEGORIES:
            return CATEGORY
        return TEXT

    def _find_molecule_column(self) -> str | None:
        """The string column of SMILES, if any. Columns are tried by name (`smiles`,
        then names containing "smiles", then `molecule`/`mol`, then the rest), and
        the first whose sampled values mostly parse as SMILES wins."""
        strings = [k for k, t in self.df.schema.items() if t == polars.String]

        def priority(key: str) -> int:
            name = key.lower()
            if name == "smiles":
                return 0
            if "smiles" in name:
                return 1
            if name in ("molecule", "mol"):
                return 2
            return 3

        for key in sorted(strings, key=priority):
            named = priority(key) <= 1
            if _looks_like_smiles(
                self.df[key],
                MOLECULE_MIN_VALID_NAMED if named else MOLECULE_MIN_VALID,
            ):
                return key
        return None

    def _find_structure_column(self) -> str | None:
        """The string column of crystal structures, if any: one named `structure`
        (as in Simmate's database tables) whose sampled values mostly parse as
        POSCAR or CIF text."""
        for key, dtype in self.df.schema.items():
            if (
                key.lower() != "structure"
                or key == self.molecule_column
                or dtype != polars.String
            ):
                continue
            values = self.df[key].drop_nulls()
            if values.is_empty():
                return None
            sample = values.head(STRUCTURE_SAMPLE).to_list()
            valid = 0
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # pymatgen warns about odd CIFs
                for value in sample:
                    # failed parses are expected here
                    with contextlib.suppress(Exception):
                        Structure.from_database_string(value)
                        valid += 1
            return key if valid >= STRUCTURE_MIN_VALID * len(sample) else None
        return None

    def _find_id_column(self) -> str | None:
        """The column that names each row (`id`, else `name`), if there is one."""
        by_name = {key.lower(): key for key in self.kinds}
        for name in ("id", "name"):
            if name in by_name:
                return by_name[name]
        return None

    def of_kind(self, *kinds: str) -> list[str]:
        """The columns of any of `kinds`, in the dataframe's order."""
        return [key for key, kind in self.kinds.items() if kind in kinds]

    @property
    def hidden_by_default(self) -> set[str]:
        """The shown columns to hide until asked for: `HIDDEN_COLUMNS`, long text
        (e.g. mol blocks, which would make very wide columns), and the SMILES column,
        which the structure images already show."""
        hidden = (HIDDEN_COLUMNS & set(self.shown)) | self.long_text
        if self.molecule_column is not None:
            hidden.add(self.molecule_column)
        return hidden

    @property
    def shown(self) -> list[str]:
        """The columns that can be shown as text (e.g. in the table): every column
        but internal, object, binary and all-null ones. The ID column (if any)
        comes first, then the rest in the dataframe's order."""
        keys = [
            key
            for key, dtype in self.df.schema.items()
            if key not in INTERNAL_COLUMNS
            and dtype not in (polars.Object, polars.Binary, polars.Null)
        ]
        if self.id_column in keys:
            keys.remove(self.id_column)
            keys.insert(0, self.id_column)
        return keys

    @property
    def searched(self) -> list[str]:
        """The columns the text search looks in."""
        return [
            key
            for key in self.of_kind(TEXT, CATEGORY, MOLECULE)
            if key not in self.long_text and self.df.schema[key] == polars.String
        ]

    # --- values ---------------------------------------------------------------------------

    def label(self, row: int) -> str:
        """What to call a row, e.g. above its card: its ID, or its row number."""
        if self.id_column is None:
            return f"Row {row + 1}"
        if self._labels is None:
            self._labels = self.df[self.id_column].to_list()
        value = self._labels[row]
        return f"Row {row + 1}" if value is None else str(value)

    def numbers(self, key: str) -> np.ndarray:
        """A number or date column as floats, one per row (dates as UTC epoch
        seconds), with NaN for nulls."""
        if key not in self._numbers:
            if self.kinds[key] == DATE:
                column = self._dates.get(key, self.df[key])
                if column.dtype == polars.Date:
                    column = column.cast(polars.Datetime("ms"))
                values = column.dt.epoch("s")
            else:
                values = self.df[key]
            self._numbers[key] = (
                values.cast(polars.Float64).fill_null(np.nan).to_numpy()
            )
        return self._numbers[key]

    def bounds(self, key: str) -> tuple[float, float] | None:
        """The smallest and largest of a number or date column (as from `numbers`),
        or None when it has no values."""
        values = self.numbers(key)
        if np.isnan(values).all():
            return None
        return float(np.nanmin(values)), float(np.nanmax(values))

    def codes(self, key: str) -> tuple[np.ndarray, list[str]]:
        """A category column as (one code per row, the label of each code), sorted."""
        if key not in self._codes:
            values = self.strings(key)
            labels = sorted(values.unique().to_list())
            lookup = {label: code for code, label in enumerate(labels)}
            codes = np.array([lookup[v] for v in values.to_list()], dtype=int)
            self._codes[key] = (codes, labels)
        return self._codes[key]

    def strings(self, key: str) -> polars.Series:
        """A column as text, with "None" for nulls, as category labels show it."""
        return self.df[key].cast(polars.String).fill_null("None")

    def view_range(self, key: str, low: float, high: float) -> tuple[str, float, float]:
        """A plot's visible span of `key` (as from `numbers`), for
        `CompoundFilterProxy.set_view_ranges`. Dates are rounded in to whole days, so
        a point at midnight just outside isn't kept."""
        if self.kinds[key] != DATE:
            return key, low, high
        return (
            key,
            np.ceil(low / SECONDS_PER_DAY) * SECONDS_PER_DAY,
            # through the end of the last whole day shown
            (np.floor(high / SECONDS_PER_DAY) + 1) * SECONDS_PER_DAY - 1,
        )

    def range_mask(
        self, key: str, low: float, high: float, keep_missing: bool = False
    ) -> np.ndarray:
        """By row: True where `key` (as from `numbers`) is within [low, high]. Rows
        missing a value (null) are False, or True when `keep_missing`."""
        values = self.numbers(key)
        with np.errstate(invalid="ignore"):  # comparisons with NaN are False
            mask = (values >= low) & (values <= high)
        if keep_missing:
            mask |= np.isnan(values)
        return mask


def to_date(seconds: float) -> datetime.date:
    """UTC epoch seconds (as from `DataColumns.numbers`) as the date they fall on."""
    days = int(np.clip(np.floor(seconds / SECONDS_PER_DAY), -700_000, 2_900_000))
    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)


def to_seconds(date: datetime.date) -> float:
    """The start of `date` (UTC) as epoch seconds, the inverse of `to_date`."""
    return float((date - datetime.date(1970, 1, 1)).days * SECONDS_PER_DAY)


def _looks_like_smiles(column: polars.Series, min_valid: float) -> bool:
    """Whether at least `min_valid` of a sample of the column's values parse as SMILES."""
    values = column.drop_nulls()
    if values.is_empty():
        return False
    sample = values.sample(min(MOLECULE_SAMPLE, values.len()), seed=0).to_list()
    RDLogger.DisableLog("rdApp.*")  # failed parses are expected here
    try:
        valid = sum(
            # unsanitized: only checks the syntax, which is all we need and fast
            Chem.MolFromSmiles(value, sanitize=False) is not None
            for value in sample
            if value and "\n" not in value  # e.g. mol blocks
        )
    finally:
        RDLogger.EnableLog("rdApp.*")
    return valid >= min_valid * len(sample)
