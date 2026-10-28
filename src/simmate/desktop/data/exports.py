import re
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import polars

from simmate.desktop.data.columns import INTERNAL_COLUMNS
from simmate.desktop.data.dataset import ToolkitDataset
from simmate.toolkit import Molecule, Structure

TABLES = "Tables"
MOLECULES = "Molecules"
CRYSTALS = "Crystals"

# An Excel sheet holds at most 1,048,576 rows, one of which is the header.
EXCEL_MAX_ROWS = 1_048_575


@dataclass
class ExportFormat:
    """
    One option in the Export panel: a file type the whole dataset can be saved as.
    See `EXPORT_FORMATS`, `write_table` and `write_records`.
    """

    name: str  # as listed in the panel
    section: str
    key: str  # what it's known by in `write_table` and `write_records`
    suffix: str  # of the saved file
    description: str = ""
    slow: bool = False
    per_row: bool = False
    """Whether it's written a record at a time by `write_records`, as each row's
    structure has to be read, rather than in one go by `write_table`."""


EXPORT_FORMATS = [
    ExportFormat(
        "CSV",
        TABLES,
        "csv",
        ".csv",
        "Comma-separated text, which most programs can open. Lists are joined with "
        "semicolons and fingerprints are written as hex.",
    ),
    ExportFormat(
        "Excel",
        TABLES,
        "xlsx",
        ".xlsx",
        "A workbook of one sheet. Lists are joined with semicolons and fingerprints "
        "are written as hex.",
    ),
    ExportFormat(
        "Parquet",
        TABLES,
        "parquet",
        ".parquet",
        "A compact table that keeps every column's type (e.g. fingerprints), and "
        "opens fastest in Simmate",
    ),
    ExportFormat(
        "SDF",
        MOLECULES,
        "sdf",
        ".sdf",
        "2D structures, with every other column as a property",
        per_row=True,
    ),
    ExportFormat(
        "SMILES",
        MOLECULES,
        "smi",
        ".smi",
        "One SMILES per line, then its ID (when the dataset has one)",
    ),
    ExportFormat(
        "XYZ (3D)",
        MOLECULES,
        "xyz",
        ".zip",
        "A zip of one .xyz file per molecule, of a 3D conformer made for it "
        "(ETKDG, then MMFF)",
        slow=True,
        per_row=True,
    ),
    ExportFormat(
        "CIF",
        CRYSTALS,
        "cif",
        ".zip",
        "A zip of one .cif file per structure",
        per_row=True,
    ),
    ExportFormat(
        "POSCAR",
        CRYSTALS,
        "poscar",
        ".zip",
        "A zip of one VASP POSCAR (.vasp) file per structure",
        per_row=True,
    ),
]


def write_table(dataset: ToolkitDataset, fmt: ExportFormat, path: Path):
    """
    Saves every row of `dataset` to `path` as `fmt`, one of the formats written in
    one go (see `ExportFormat.per_row`). It's fast and mostly runs outside Python,
    so it suits a background thread.
    """
    df = _exported(dataset.df)
    if fmt.key == "csv":
        _text_columns(df).write_csv(path)
    elif fmt.key == "xlsx":
        df = _text_columns(df)
        # Excel can't store time zones, so datetimes are given in UTC
        df = df.with_columns(
            polars.col(key).dt.convert_time_zone("UTC").dt.replace_time_zone(None)
            for key, dtype in df.schema.items()
            if isinstance(dtype, polars.Datetime) and dtype.time_zone
        )
        df.write_excel(path)
    elif fmt.key == "parquet":
        df.write_parquet(path)
    elif fmt.key == "smi":
        # as `read_smi` reads them back: the SMILES, then the ID after a tab
        keys = [dataset.molecule_column]
        id_column = dataset.columns.id_column
        if id_column is not None and id_column != dataset.molecule_column:
            keys.append(id_column)
        df.select(keys).drop_nulls(dataset.molecule_column).write_csv(
            path, separator="\t", include_header=False, quote_style="never"
        )
    else:
        raise ValueError(f"{fmt.name} is written a row at a time (`write_records`)")


def write_records(
    dataset: ToolkitDataset,
    fmt: ExportFormat,
    path: Path,
    skipped: list[int],
) -> Iterator[int]:
    """
    Saves every row of `dataset` to `path` as `fmt`, one of the formats written a
    record at a time (see `ExportFormat.per_row`), as each needs its row's
    structure read. Rows whose structure can't be read (or, for XYZ, made 3D) are
    left out, and their row numbers added to `skipped`.

    It's a generator: it yields the number of rows done after each one, letting a
    caller spread the work out (e.g. between UI events, see `IncrementalTask`).
    Exhaust it to write the whole file. Closing it early (`close()`) closes the file.
    """
    df = _exported(dataset.df)

    if fmt.key == "sdf":
        # the structure is the mol block, and every other column a property
        properties = _text_columns(df.drop(dataset.molecule_column))
        with Path(path).open("w") as file:
            for row, (smiles, values) in enumerate(
                zip(df[dataset.molecule_column], properties.iter_rows(named=True))
            ):
                try:
                    file.write(Molecule.from_smiles(smiles).to_sdf(properties=values))
                except Exception:
                    skipped.append(row)
                yield row + 1
        return

    # The rest are zips of one file per row, named by its ID
    if fmt.key == "xyz":
        values, extension = df[dataset.molecule_column], ".xyz"
    elif fmt.key in ("cif", "poscar"):
        values = df[dataset.structure_column]
        extension = ".cif" if fmt.key == "cif" else ".vasp"
    else:
        raise ValueError(f"{fmt.name} is written in one go (`write_table`)")
    id_column = dataset.columns.id_column
    ids = df[id_column].to_list() if id_column is not None else [None] * df.height
    used = set()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row, (value, id_) in enumerate(zip(values, ids)):
            try:
                if fmt.key == "xyz":
                    molecule = Molecule.from_smiles(value)
                    # the 3D card's seed, so files match the conformers it shows
                    molecule.convert_to_3d(keep_hydrogen=True, random_seed=0xF00D)
                    text = molecule.to_xyz()
                else:
                    text = Structure.from_database_string(value).to(fmt=fmt.key)
            except Exception:
                skipped.append(row)
                yield row + 1
                continue
            # its ID, made safe for a file name and unique (else its row number)
            stem = "" if id_ is None else re.sub(r"[^\w.-]+", "_", str(id_))
            stem = stem or f"row_{row + 1}"
            name, number = stem, 2
            while name in used:
                name, number = f"{stem}_{number}", number + 1
            used.add(name)
            archive.writestr(name + extension, text)
            yield row + 1


def _exported(df: polars.DataFrame) -> polars.DataFrame:
    """The columns of `df` that are saved: all but internal and object ones."""
    return df.select(
        key
        for key, dtype in df.schema.items()
        if key not in INTERNAL_COLUMNS and dtype != polars.Object
    )


def _text_columns(df: polars.DataFrame) -> polars.DataFrame:
    """
    `df`, with the columns that text formats can't hold as text: lists joined with
    semicolons (as the Featurize panel joins SMARTS matches), fingerprints (binary)
    as hex, and all-null columns as strings.
    """
    casts = []
    for key, dtype in df.schema.items():
        if isinstance(dtype, polars.List | polars.Array):
            casts.append(
                polars.col(key).cast(polars.List(polars.String)).list.join("; ")
            )
        elif dtype == polars.Binary:
            casts.append(polars.col(key).bin.encode("hex"))
        elif dtype == polars.Null:
            casts.append(polars.col(key).cast(polars.String))
    return df.with_columns(casts)
