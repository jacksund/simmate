import datetime

import numpy as np
import polars

NUMBER = "number"
DATE = "date"
CATEGORY = "category"

# String columns with at most this many distinct values count as categories (e.g.
# a series or status); ones with more (IDs, SMILES) can't be plotted.
MAX_CATEGORIES = 20

DATE_FORMAT = "%Y-%m-%d"
SECONDS_PER_DAY = 86_400


class DataColumns:
    """What each of a dataframe's columns can be plotted as, and its values to plot.

    Every column gets a kind, worked out from its values rather than a fixed list:

    - `NUMBER`: ints and floats.
    - `DATE`: dates, or strings that are all ISO dates (e.g. "2026-03-14").
    - `CATEGORY`: strings or booleans with at most `MAX_CATEGORIES` distinct values.

    Other columns (IDs, SMILES, objects) are left out. Values are cached per column,
    as plots ask for them on every redraw.
    """

    def __init__(self, df: polars.DataFrame):
        self.df = df
        self.kinds: dict[str, str] = {}
        self._dates: dict[str, polars.Series] = {}  # parsed, for string date columns
        for key, dtype in df.schema.items():
            kind = self._kind(key, dtype)
            if kind:
                self.kinds[key] = kind
        self._numbers: dict[str, np.ndarray] = {}
        self._codes: dict[str, tuple[np.ndarray, list[str]]] = {}

    def _kind(self, key: str, dtype) -> str | None:
        if dtype.is_numeric():
            return NUMBER
        if dtype in (polars.Date, polars.Datetime):
            return DATE
        if dtype == polars.Boolean:
            return CATEGORY
        if dtype != polars.String:
            return None
        column = self.df[key]
        dates = column.str.to_date(DATE_FORMAT, strict=False)
        if column.null_count() < column.len() and (
            dates.null_count() == column.null_count()
        ):
            self._dates[key] = dates
            return DATE
        if column.n_unique() <= MAX_CATEGORIES:
            return CATEGORY
        return None

    def of_kind(self, *kinds: str) -> list[str]:
        """The columns of any of `kinds`, in the dataframe's order."""
        return [key for key, kind in self.kinds.items() if kind in kinds]

    def numbers(self, key: str) -> np.ndarray:
        """A number or date column as floats, one per row (dates as UTC epoch seconds)."""
        if key not in self._numbers:
            if self.kinds[key] == DATE:
                column = self._dates.get(key, self.df[key])
                values = column.cast(polars.Datetime("ms")).dt.epoch("s")
            else:
                values = self.df[key]
            self._numbers[key] = values.cast(polars.Float64).to_numpy()
        return self._numbers[key]

    def codes(self, key: str) -> tuple[np.ndarray, list[str]]:
        """A category column as (one code per row, the label of each code), sorted."""
        if key not in self._codes:
            values = self.df[key].cast(polars.String).fill_null("None")
            labels = sorted(values.unique().to_list())
            lookup = {label: code for code, label in enumerate(labels)}
            codes = np.array([lookup[v] for v in values.to_list()], dtype=int)
            self._codes[key] = (codes, labels)
        return self._codes[key]

    def view_range(
        self, key: str, low: float, high: float
    ) -> tuple[str, object, object]:
        """A plot's visible span of `key` (as from `numbers`), as the column's own
        values, ready for `CompoundFilterProxy.set_view_ranges`."""
        if self.kinds[key] != DATE:
            return key, low, high
        # whole days shown: round in, so a point at midnight just outside isn't kept
        first, last = _to_date(np.ceil(low / SECONDS_PER_DAY)), _to_date(
            np.floor(high / SECONDS_PER_DAY)
        )
        if key in self._dates:  # stored as ISO strings, which sort like dates
            return key, first.isoformat(), last.isoformat()
        return key, first, last

    def format(self, key: str, value: float) -> str:
        """`value` (as from `numbers`) for display, e.g. in the status bar."""
        if self.kinds.get(key) == DATE:
            return _to_date(np.floor(value / SECONDS_PER_DAY)).isoformat()
        return f"{value:.4g}"


def _to_date(days: float) -> datetime.date:
    days = int(np.clip(days, -700_000, 2_900_000))  # within date's range
    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
