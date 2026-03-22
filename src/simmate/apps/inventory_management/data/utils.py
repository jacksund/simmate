# -*- coding: utf-8 -*-

import tempfile
import zipfile
from pathlib import Path

import pandas


def load_substances_data() -> pandas.DataFrame:
    zip_path = Path(__file__).parent / "substances.zip"

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            # Extract only the specific file to the temp directory
            z.extract("substances.csv", path=tmp)
            return pandas.read_csv(Path(tmp) / "substances.csv")


DEFAULT_SUBSTANCES = load_substances_data()
