# -*- coding: utf-8 -*-

import json
import logging
import shutil
import urllib
import warnings
from pathlib import Path

import polars

from simmate.config import settings
from simmate.utils import dispatch


class ArchiveMixin:
    """
    A mixin that adds archiving functionality to a database table. This includes
    methods for exporting data to a compressed zip file and importing it back.
    """

    archive_fields: list[str] = []
    """
    The base information for this database table and only these fields are stored
    when the `to_archive` method is used. Columns excluded from this list can 
    be calculated quickly and will therefore not be stored. Therefore, this list
    can be thought of as the "raw data".
    
    The columns from mix-ins will automatically be added. If you would like to
    remove one of these columns, you can add "--" to the start of the column
    name (e.g. "--energy" will not store the energy).
    
    To see all archive fields, see the `archive_fieldset` property.
    """

    @classmethod
    def to_archive(
        cls,
        filename: Path | str = None,
        format: str = "csv",
        columns: str | list[str] = "minimal",
    ):
        """
        Writes the entire database table to an archive file. If you prefer
        a subset of entries for the archive, use the to_archive method
        on your SearchResults instead (e.g. MyTable.objects.filter(...).to_archive())

        #### Parameters

        - `filename`:
            The filename to write the zip file to. Auto-generated if not provided.
        - `format`:
            The file format to export. Options are "csv" (default) or "parquet".
        - `columns`:
            Which columns to include. Options are "minimal" (archive_fieldset),
            "full" (all columns), or a custom list of column names.
        """
        cls.objects.all().to_archive(filename, format=format, columns=columns)

    @classmethod
    @property
    def archive_fieldset(cls) -> list[str]:
        all_fields = ["id", "updated_at", "created_at", "source"]

        # If calling this method on the base class, just return the sole mix-in.
        # Note: we use __name__ to avoid circular imports with DatabaseTable
        if cls.__name__ == "DatabaseTable":
            return all_fields

        # Otherwise we need to go through the mix-ins and add their fields to
        # the list
        all_fields += [
            field for mixin in cls.get_mixins() for field in mixin.archive_fields
        ]

        # Sometimes a column will be disabled by adding "--" in front of the
        # column name. For example, "--band_gap" would exclude storing the band
        # gap in the archive. We look for any columns that start with this
        # and then remove them
        for field in cls.archive_fields:
            if field.startswith("--"):
                all_fields.remove(field.removeprefix("--"))
            else:
                all_fields.append(field)

        # Some tables delete the columns that a mixin or base table provides.
        # For example, the "source" column is deleted sometimes because
        # the entire table comes from a fixed source (e.g. JARVIS or the
        # MatProj). We check this with all default columns, just in case.
        all_fields = [f for f in all_fields if f in cls.get_column_names()]

        # and remove accidental duplicate cols if any
        all_fields = list(set(all_fields))

        return all_fields

    # -------------------------------------------------------------------------
    # Methods that handle loading results from archives
    # -------------------------------------------------------------------------

    remote_archive_link: str = None
    """
    The URL that is used to download the archive and then populate this table.
    Many tables have pre-existing data that you can download and load into 
    your local database, so if this attribute is set, you can use the 
    `load_remote_archive` method.
    """

    @classmethod
    def _load_single_entry(cls, entry):
        """
        Quick utility function that loads a single entry to the database.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # BUG: some columns don't properly convert to python objects, but
            # it seems inconsistent when this is done... For now I just manually
            # convert JSON columns
            json_parsing_columns = ["site_forces", "lattice_stress"]
            for column in json_parsing_columns:
                if column in entry:
                    if entry[column]:  # sometimes it has a value of None
                        entry[column] = json.loads(entry[column])
            # OPTIMIZE: consider applying this to the df column for faster loading

            return cls.from_toolkit(**entry)

    # @transaction.atomic  # We can't have an atomic transaction if we use Dask
    @classmethod
    def load_archive(
        cls,
        filename: str | Path = None,
        delete_on_completion: bool = False,
        parallel: bool | str = False,
    ):
        """
        Reads a compressed zip file made by `objects.to_archive` and loads the data
        back into the Simmate database.

        Typically, users won't call this method directly, but instead use the
        `load_remote_archive` method, which handles downloading the archive
        file from the Simmate website for you.

        #### Parameters

        - `filename`:
            The filename to write the zip file to. By defualt, None will try to
            find a file named "MyExampleTableName-2022-01-25.zip", where the date
            corresponds to version/timestamp. If multiple files match this format
            the most recent date will be used.

        - `delete_on_completion`:
            Whether to delete the archive file once all data is loaded into the
            database. Defaults to False

        - `parallel`:
            How to dispatch the data loading. False will load one by one.
            True or "core" will start a ProcessPoolExecutor.
        """

        # We disable warnings while loading archives because pymatgen prints
        # a lot of them (for things like rounding or electronegativity alerts).
        # We use a context manager to ensure we don't affect the rest of the
        # user's session.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # generate the file name if one wasn't given
            if not filename:
                # The name will be something like "MyExampleTable-2022-01-25.zip".
                # We go through all files that match "MyExampleTable-*.zip" and then
                # grab the most recent date.
                matching_files = [
                    file
                    for file in Path.cwd().iterdir()
                    if file.name.startswith(cls.table_name) and file.suffix == ".zip"
                ]
                # make sure there is at least one file
                if not matching_files:
                    raise FileNotFoundError(
                        f"No file found matching the {cls.table_name}-*.zip format"
                    )
                # sort the files by date and grab the first
                matching_files.sort(reverse=True)
                filename = matching_files[0]

            # Turn the filename into the full path -- which makes a number of
            # manipulations easier below.
            filename = Path(filename).absolute()

            # uncompress the zip file to the same directory that it is located in
            shutil.unpack_archive(
                filename,
                extract_dir=filename.parent,
            )

            # Determine the inner file format. For old-style archives
            # (Table-date.zip), the inner file is Table-date.csv. For new-style
            # archives (Table-date.parquet.zip), stripping .zip gives
            # Table-date.parquet directly.
            inner_filename = filename.with_suffix("")  # strips .zip
            if inner_filename.suffix == ".parquet":
                # New-style: "Table-date.parquet.zip" → "Table-date.parquet"
                df = polars.read_parquet(inner_filename)
            else:
                # Old-style: "Table-date.zip" → look for "Table-date.csv"
                inner_filename = inner_filename.with_suffix(".csv")
                df = polars.read_csv(inner_filename)

            # convert the dataframe to a list of dictionaries that we will iterate
            # through. Polars natively converts nulls to None when calling to_dicts.
            entries = df.to_dicts()

            # now iterate through all entries to save them to the database
            db_objects = dispatch(
                entries,
                cls._load_single_entry,
                parallel=parallel,
                batch_size=15000,
            )

            cls.objects.bulk_create(
                db_objects,
                batch_size=15000,
                ignore_conflicts=True,
            )

            # We can now delete the files. The zip file is only deleted if requested.
            inner_filename.unlink()
            if delete_on_completion:
                filename.unlink()  # the zip archive

    @classmethod
    def load_remote_archive(
        cls,
        remote_archive_link: str = None,
        parallel: bool | str = False,
    ):
        """
        Downloads a compressed zip file made by `objects.to_archive` and loads
        the data back into the Simmate database.

        This method should only be called once -- when you have a completely
        empty database. After this call, all data will be stored locally and
        you don't need to call this method again (even accross python sessions).

        #### Parameters

        - `remote_archive_link`:
            The URL for that the archive will be downloaded from. If not supplied,
            it will default to the table's remote_archive_link attribute.

        - `parallel`:
            How to dispatch the data loading. False will load one by one.
            True or "core" will start a ProcessPoolExecutor.
        """

        # confirm that we have a link to download from
        if not remote_archive_link:
            # if no link was given we take the input value from class attribute
            if not cls.remote_archive_link:
                raise Exception(
                    "This table does not have a default link to load the archive "
                    " from. You must provide a remote_archive_link."
                )
            remote_archive_link = cls.remote_archive_link

        # tell the user where the data comes from
        if cls._meta.app_label == "data_explorer":
            logging.warning(
                "this data is NOT from the Simmate team, so be sure "
                "to visit the provider's website and to cite their work."
                f" This data is from {getattr(cls, 'source', 'the provider')} "
                f"and the following paper should be cited: {getattr(cls, 'source_doi', '---')}"
            )

        # Predetermine the file name, which is just the ending of the URL
        archive_filename = remote_archive_link.split("/")[-1]

        # Determine the target directory for the download
        # Example: ~/simmate/cod/archive/CodStructure-2026-03-20.zip
        app_label = cls._meta.app_label
        archive_dir = settings.config_directory / app_label / "archive"
        archive_path = archive_dir / archive_filename

        # Download the archive zip file from the URL if it doesn't already exist
        if archive_path.exists():
            logging.info(
                f"Archive already exists at {archive_path}. Skipping download."
            )
        else:
            logging.info(f"Downloading archive file to {archive_path}...")
            # ensure the directory exists
            archive_dir.mkdir(parents=True, exist_ok=True)
            # download the file
            urllib.request.urlretrieve(remote_archive_link, archive_path)
            logging.info("Done.")

        # now that the archive is downloaded, we can load it into our db
        logging.info("Loading data into Simmate database")
        cls.load_archive(
            archive_path,
            delete_on_completion=False,
            parallel=parallel,
        )
        logging.info("Done.")

    # -------------------------------------------------------------------------
    # Methods that handle building and uploading archives
    # -------------------------------------------------------------------------

    @classmethod
    def export_and_upload(
        cls,
        format: str = "csv",
        columns: str | list[str] = "full",
        s3_bucket: type = None,
    ):
        """
        Exports the database table to an archive file and uploads it to S3.

        The archive is written to the local config directory at
        `<simmate-config>/<app>/archive/<file>` and is kept after upload.

        This is the primary utility for building the downloadable files
        shown on the data explorer homepage.

        #### Parameters

        - `format`:
            The export format to use. Defaults to "csv".

        - `columns`:
            Which columns to include. Options are:
            - "full": All columns in the table (default)
            - "minimal": Only the archive_fieldset columns
            - A custom list of column names

        - `s3_bucket`:
            The S3Bucket class to upload to. Defaults to SimmateS3Bucket.

        #### Example

            ```python
            from simmate.apps.cod.models import CodStructure
            CodStructure.export_and_upload()
            ```
        """
        from simmate.database.external_connectors.s3 import SimmateS3Bucket

        if s3_bucket is None:
            s3_bucket = SimmateS3Bucket

        app_label = cls._meta.app_label
        s3_prefix = f"{app_label}/archive"

        # Determine the local archive directory
        archive_dir = settings.config_directory / app_label / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"Exporting {cls.table_name} as {format}...")

        # Use to_archive to build the file locally in the archive directory.
        # We pass a filename so it writes to the correct location.
        from datetime import datetime

        today = datetime.today()
        columns_label = (
            "full"
            if columns == "full"
            else "minimal" if columns == "minimal" else "custom"
        )
        filename_base = "-".join(
            [
                cls.table_name,
                columns_label,
                str(today.year),
                str(today.month).zfill(2),
                str(today.day).zfill(2),
            ]
        )
        archive_file = archive_dir / f"{filename_base}.{format}.zip"

        cls.to_archive(filename=archive_file, format=format, columns=columns)

        # Upload to S3
        s3_key = f"{s3_prefix}/{archive_file.name}"
        logging.info(f"Uploading {archive_file.name} to s3://{s3_key}...")
        s3_bucket.upload_file(archive_file, s3_key)
        logging.info(f"Uploaded {archive_file.name}")

        logging.info(f"Export and upload complete for {cls.table_name}.")
