# -*- coding: utf-8 -*-

import json
import logging
import shutil
import urllib
import warnings
from pathlib import Path

import pandas
from rich.progress import track

from simmate.config import settings


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
    def to_archive(cls, filename: Path | str = None):
        """
        Writes the entire database table to an archive file. If you prefer
        a subset of entries for the archive, use the to_archive method
        on your SearchResults instead (e.g. MyTable.objects.filter(...).to_archive())
        """
        cls.objects.all().to_archive(filename)

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

    # @transaction.atomic  # We can't have an atomic transaction if we use Dask
    @classmethod
    def load_archive(
        cls,
        filename: str | Path = None,
        delete_on_completion: bool = False,
        parallel: bool = False,
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
            Whether to load the data in parallel. If true, this will start
            a local Dask cluster and each data row will be submitted as a task
            to the cluster. This provides substansial speed-ups for loading
            large datasets into the dataset. Default is False.
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

            # We will now have a csv file of the same name, which we load into
            # a pandas dataframe
            csv_filename = filename.with_suffix(".csv")  # was ".zip"
            df = pandas.read_csv(csv_filename)

            # BUG: NaN values throw errors when read into SQL databases, so we
            # convert all NaN entries to None. This hacky line was taken from
            #   https://stackoverflow.com/questions/39279824/
            df = df.astype(object).where(df.notna(), None)

            # convert the dataframe to a list of dictionaries that we will iterate
            # through.
            entries = df.to_dict(orient="records")

            # to enable parallelization, we define a function to load a single
            # entry (or row) of data. This allows us to submit the function to Dask.
            def load_single_entry(entry):
                """
                Quick utility function that load a single entry to the database.
                We have this as a internal function in order to allow submitting
                this function to Dask (for parallelization).
                """
                # We disable warnings while loading archives because pymatgen prints
                # a lot of them (for things like rounding or electronegativity alerts).
                # This is especially important for parallel workers which may not
                # inherit the warning filter from the main process.
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

            # now iterate through all entries to save them to the database
            if not parallel:
                # If user doesn't want parallelization, we run these in the main
                # thread and monitor progress
                db_objects = [load_single_entry(entry) for entry in track(entries)]

            # otherwise we use dask to submit these in batches!
            else:

                from simmate.config.dask import batch_submit

                db_objects = batch_submit(
                    function=load_single_entry,
                    args_list=entries,
                    batch_size=15000,
                )

            cls.objects.bulk_create(
                db_objects,
                batch_size=15000,
                ignore_conflicts=True,
            )

            # We can now delete the files. The zip file is only deleted if requested.
            csv_filename.unlink()
            if delete_on_completion:
                filename.unlink()  # the zip archive

    @classmethod
    def load_remote_archive(
        cls,
        remote_archive_link: str = None,
        parallel: bool = False,
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
            Whether to load the data in parallel. If true, this will start
            a local Dask cluster and each data row will be submitted as a task
            to the cluster. This provides substansial speed-ups for loading
            large datasets into the dataset. Default is False.
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
            logging.info(f"Archive already exists at {archive_path}. Skipping download.")
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
