from pathlib import Path

import polars

READ_SUFFIXES = (".parquet", ".csv", ".sdf", ".smi")


def read_table(path: Path) -> polars.DataFrame:
    """
    Reads a dataset file as a table. Parquet and CSV files are read as they are;
    SDF and SMILES files become one row per molecule (see `read_sdf`, `read_smi`).
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return polars.read_parquet(path)
    if suffix == ".csv":
        return polars.read_csv(path, infer_schema_length=10_000)
    if suffix == ".sdf":
        return read_sdf(path)
    if suffix == ".smi":
        return read_smi(path)
    raise ValueError(f"Can't read {path.name}: use one of {', '.join(READ_SUFFIXES)}")


def read_sdf(path: Path) -> polars.DataFrame:
    """An SDF file as a table: one row per molecule, of its SMILES and properties."""
    from simmate.toolkit import Molecule

    molecules = Molecule.from_sdf_file(path, skip_failed=True)
    if not isinstance(molecules, list):
        molecules = [molecules]
    rows = [
        {
            "smiles": molecule.to_smiles(),
            # as text, then typed per column below (rdkit guesses per molecule)
            **{
                key: str(value)
                for key, value in molecule.metadata.items()
                if not key.startswith("_")  # rdkit's private props, e.g. _Name
            },
        }
        for molecule in molecules
    ]
    df = polars.from_dicts(rows, infer_schema_length=None)
    return df.with_columns(
        _parse_numbers(df[column]) for column in df.columns if column != "smiles"
    )


def read_smi(path: Path) -> polars.DataFrame:
    """
    A SMILES file as a table: one row per line, of its SMILES and (when the file
    has them) the name after it. Blank lines and `#` comments are skipped.
    """
    smiles, names = [], []
    with Path(path).open() as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            smiles.append(parts[0])
            names.append(parts[1] if len(parts) > 1 else None)
    columns = {"smiles": smiles}
    if any(names):
        columns["name"] = names
    return polars.DataFrame(columns, schema={key: polars.String for key in columns})


def _parse_numbers(column: polars.Series) -> polars.Series:
    """`column` as integers or floats if every value is one, else unchanged."""
    for dtype in (polars.Int64, polars.Float64):
        try:
            return column.cast(dtype)
        except polars.exceptions.InvalidOperationError:
            continue
    return column
