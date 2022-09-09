# -*- coding: utf-8 -*-

"""
This module defines the lowest-level classes for database tables and their
search results.

See the `simmate.database.base_data_types` (which is the parent module of 
this one) for example usage.
"""

import inspect
import json
import logging
import shutil
import urllib
import warnings
from functools import cache
from pathlib import Path

import pandas
import yaml
from django.db import models  # , transaction
from django.db import models as table_column
from django.utils.module_loading import import_string
from django.utils.timezone import datetime
from django_filters import rest_framework as django_api_filters
from django_pandas.io import read_frame
from rich.progress import track

# The "as table_column" line does NOTHING but rename a module.
# I have this because I want to use "table_column.CharField(...)" instead
# of "models.CharField(...)" in my Models. This let's beginners read my
# higher level classes and instantly understand what each thing represents
# -- without them needing to understand that Django Model == Database Table.
# Experts may find this annoying, so I'm sorry :(


class SearchResults(models.QuerySet):
    """
    This class adds some extra methods to the results returned from a database
    search. For example, if you searched all Structures and wanted to convert
    these to a pandas dataframe or even a list of pymatgen structures, you can
    now do...

    ``` python
    # for a list of database objects (django models)
    search_results = Structures.objects.all()

    # for a pandas dataframe (which is like an Excel table)
    dataframe = search_results.to_dataframe()

    # for a list of pymatgen structure objects
    structures = search_results.to_toolkit()
    ```

    All other functionality is inherited from
    [Django QuerySets](https://docs.djangoproject.com/en/4.0/ref/models/querysets/).
    """

    def to_dataframe(
        self,
        fieldnames: list[str] = (),
        verbose: bool = True,
        index: str = None,
        coerce_float: str = False,
        datetime_index: str = False,
    ) -> pandas.DataFrame:
        """
        Returns a Pandas DataFrame of the search results

        This method is coppied from django_pandas'
        [manager.py](https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py)

        Paramaters
        -----------
        - `fieldnames`:
            The model field names(columns) to utilise in creating the DataFrame.
            You can span a relationships in the usual Django ORM way by using
            the foreign key field name separated by double underscores and refer
            to a field in a related model.
        - `index`:
            specify the field to use  for the index. If the index field is not
            in fieldnames it will be appended. This is mandatory for timeseries.
        - `verbose`:
            If  this is `True` then populate the DataFrame with the human
            readable versions for foreign key fields else use the actual values
            set in the model
        - `coerce_float`:
            Attempt to convert values to non-string, non-numeric objects (like
            decimal.Decimal) to floating point.
        - `datetime_index`: bool
            specify whether index should be converted to a DateTimeIndex.
        """

        # BUG: read_frame runs a NEW query, so it may be a different length from
        # the original queryset.
        # See https://github.com/chrisdev/django-pandas/issues/138 for issue
        return read_frame(
            self,
            fieldnames=fieldnames,
            verbose=verbose,
            index_col=index,
            coerce_float=coerce_float,
            datetime_index=datetime_index,
        )

    def to_toolkit(
        self,
    ) -> list:  # type of object varies (e.g. Structure, BandStructure, etc.)
        """
        Converts your SearchResults to a list of pymatgen objects
        """

        # This method will only be for structures and other classes that
        # support this method. So we make sure the model has supports it first.
        if not hasattr(self.model, "to_toolkit"):
            raise Exception(
                "This database table does not have a to_toolkit method implemented"
            )

        # now we can iterate through the queryset and return the converted
        # pymatgen objects as a list
        return [obj.to_toolkit() for obj in self]

    def to_archive(self, filename: Path | str = None):
        """
        Writes a compressed zip file using the table's `archive_fieldset`
        attribute. Underneath, the file is written in a csv format.

        This is useful for small making archive files and reloading fixtures
        to a separate database.

        This method is attached to the table manager for scenarios to allow
        queryset filtering before dumping data.

        To load this database dump into a new database, use the class's
        `from_archive` method.

        #### Parameters

        - `filename`:
            The filename to write the zip file to. By defualt, None will make
            a filename named MyExampleTableName-2022-01-25.zip, where the date
            will be the current day (for versioning).
        """

        # Generate the file name if one wasn't given.
        if not filename:
            # This is automatically the name of the table plus the date, where
            # the date is for versioning. For example...
            #   MyExampleTable-2022-01-25
            today = datetime.today()
            filename_base = "-".join(
                [
                    self.model.table_name,
                    str(today.year),
                    str(today.month).zfill(2),
                    str(today.day).zfill(2),
                ]
            )
            filename = filename_base + ".zip"

        # convert to path obj
        filename = Path(filename)

        # grab the list of fields that we want to store
        fieldset = self.model.archive_fieldset

        # We want to load the entire table, but only grab the fields that
        # we will be storing in the archive.
        base_objs = self.only(*fieldset)

        # now convert these objects to a pandas dataframe, again using just
        # the archive columns
        df = base_objs.to_dataframe(fieldnames=fieldset)

        # Write the data to a csv file
        # OPTIMIZE: is there a better format that pandas can write to?
        csv_filename = filename.with_suffix(".csv")
        df.to_csv(csv_filename, index=False)

        # now convert the dump file to a compressed zip. In the complex, os
        # functions below we are just grabbing the filename without the
        # zip ending. We are also grabbing the directory that the csv is
        # located in
        shutil.make_archive(
            base_name=filename.with_suffix(""),  # removes .zip ending
            format="zip",
            root_dir=csv_filename.absolute().parent,
            base_dir=csv_filename.name,
        )

        # we can now delete the csv file
        csv_filename.unlink()

    def filter_by_tags(self, tags: list[str]):
        """
        A utility filter() method that
        """

        if tags:
            new_query = self
            for tag in tags:
                new_query = new_query.filter(tags__icontains=tag)
        else:
            new_query = self.filter(tags=[])
        return new_query


# Copied this line from...
# https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py
# It simply converts this queryset class to a manager.
DatabaseTableManager = models.Manager.from_queryset(SearchResults)


class DatabaseTable(models.Model):
    """
    The base class for defining a table in the Simmate database. All tables and
    mixins inherit from this class.

    Usage is identical to
    [models in Django](https://docs.djangoproject.com/en/4.0/#the-model-layer)
    where this class only adds extra methods for convenience.
    """

    class Meta:
        abstract = True

    created_at = table_column.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
    )
    """
    Timestamp of when this row was first added to the database table
    """

    updated_at = table_column.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
    )
    """
    Timestamp of when this row was was lasted changed / updated
    """

    source = table_column.JSONField(blank=True, null=True)
    """
    > Note, this field is highly experimental at the moment and subject to
    change.
    
    This column indicates where the data came from, and it could be a number 
    of things including...
     - a third party id
     - a structure from a different Simmate datbase table
     - a transformation of another structure
     - a creation method
     - a custom submission by the user
    
    By default, this is a JSON field to account for all scenarios, but some
    tables (such as those in `simmate.database.third_parties`) this is value
    should be the same for ALL entries in the table and therefore the column is
    overwritten as an attribute.
    
    For other tables where this is not a constant, here are some examples of
    values used in this column:
    
    ``` python
    # from a thirdparty database or separate table
    source = {
        "table": "MatprojStructure",
        "id": "mp-123",
    }
    
    # from a random structure creator
    source = {"method": "PyXtalStructure"}
    
    # from a templated structure creator (e.g. substituition or prototypes)
    source = {
        "method": "PrototypeStructure",
        "table": "AFLOWPrototypes",
        "id": 123,
    }
    
    # from a transformation
    source = {
        "method": "MirrorMutation",
        "table": "MatprojStructure",
        "id": "mp-123",
    }
    
    # from a multi-structure transformation
    source = {
        "method": "HereditaryMutation",
        "table": "MatprojStructure",
        "ids": ["mp-123", "mp-321"],
    }
    ```
    """
    # TODO: Explore polymorphic relations instead of a JSON dictionary.
    # Making relationships to different tables makes things difficult to use, so
    # these columns are just standalone.
    #
    # This is will be very important for "source" and "parent_nested_calculations"
    # fields because I have no way to efficiently convert these fields to the objects
    # that they refer to. There's also no good way to access a structure's "children"
    # (i.e. structure where they are the source).
    #
    # I should investigate generic relations in django though:
    # https://docs.djangoproject.com/en/3.2/ref/contrib/contenttypes/#generic-relations
    #
    # Another option is using django-polymorphic.
    # https://django-polymorphic.readthedocs.io/en/latest/
    # This thread is really helpful on the subject:
    # https://stackoverflow.com/questions/30343212/
    #
    # TODO: Consider adding some methods to track the history of a structure.
    #  This would be useful for things like evolutionary algorithms.
    # get_source_parent:
    #   this would iterate through sources until we find one in the same table
    #   as this one. Parent sources are often the most recent transformation
    #   or mutation applied to a structure, such as a MirrorMutation.
    # get_source_seed:
    #   this would iterate through sources until we hit a dead-end. So the seed
    #   source would be something like a third-party database, a method that
    #   randomly create structures, or a prototype.
    # Both of these get more complex when we consider transformation that have
    # multiple parents (and therefore multiple seeds too). An example of this
    # is the HereditaryMutation.

    source_doi: str = None
    """
    Source paper that must be referenced if this data is used. If this is None,
    please refer to the `source` attribute for further details on what to 
    reference.
    """

    remote_archive_link: str = None
    """
    The URL that is used to download the archive and then populate this table.
    Many tables, such as those in `simmate.database.third_parties`, have
    pre-existing data that you can download and load into your local database,
    so if this attribute is set, you can use the `load_remote_archive` method.
    """

    # I override the default manager with the one we define above, which has
    # extra methods useful for our querysets.
    objects = DatabaseTableManager()
    """
    Accesses all of the rows in this datatable and initiates a SearchResults
    object. Using this, you can perform complex filtering and conversions on
    data from this table.
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

    api_filters: dict = {}
    """
    Configuration of fields that can be filtered in the REST API and website 
    interface. This follows the format used by django-filters.
    
    For example...
    ``` python
    filter_fields = {
        column1=["exact"],
        column2=["range"],
        column3=BooleanFilter(...),
    }
    ```
    
    See the `api_filterset` property for the final filter object.
    """

    exclude_from_summary: list[str] = []
    """
    When writing output summaries, these columns will be ignored. This is useful
    if you have a column for storing raw data that isn't friendly to read in
    the yaml format. 'structure' is an example of a field we'd want to
    exclude because its not very readable and is available elsewhere.
    """

    # -------------------------------------------------------------------------
    # Core methods accessing key information and writing summary files
    # -------------------------------------------------------------------------

    @classmethod
    @property
    def table_name(cls) -> str:
        """
        Returns the name of this database table, which will simply match the
        class name.

        Note, we use "table_name" instead of "name" because users may want
        a column titled "name", which would break features. To reduce
        occurance of of this issue, we use "table_name" instead.
        """
        return cls.__name__

    @classmethod
    def get_column_names(cls) -> list[str]:
        """
        Returns a list of all the column names for this table and indicates which
        columns are related to other tables. This is primarily used to help
        view what data is available.
        """
        return [column.name for column in cls._meta.get_fields()]

    @classmethod
    def show_columns(cls):
        """
        Prints a list of all the column names for this table and indicates which
        columns are related to other tables. This is primarily used to help users
        interactively view what data is available.
        """
        # Iterate through and grab the columns. Note we don't use get_column_names
        # here because we are attaching relation data as well.
        column_names = [
            column.name + f" (relation to {column.related_model.table_name})"
            if column.is_relation
            else column.name
            for column in cls._meta.get_fields()
        ]

        # Then use yaml to make the printout pretty (no quotes and separate lines)
        print(yaml.dump(column_names))

    @classmethod
    def get_mixins(cls) -> list:  # -> List[DatabaseTable]
        """
        Grabs the mix-in Tables that were used to make this class. This will
        be mix-ins like Structure, Forces, etc. from the
        `simmate.database.base_data_types` module.
        """
        # this must be imported locally because it depends on all other classes
        # from this module -- and will create circular import issues if outside
        from simmate.database import base_data_types as simmate_mixins

        return [
            parent
            for parent in cls.__bases__
            if hasattr(simmate_mixins, parent.table_name)
            and parent.table_name != "DatabaseTable"
        ]

    @classmethod
    def get_mixin_names(cls) -> list[str]:
        """
        Grabs the mix-in Tables that were used to make this class and returns
        a list of their names.
        """
        return [mixin.table_name for mixin in cls.get_mixins()]

    @classmethod
    def get_extra_columns(cls) -> list[str]:
        """
        Finds all columns that aren't covered by the supported Table mix-ins.

        For example, a table made from...

        ``` python
        from simmate.database.base_data_types import (
            table_column,
            Structure,
            Forces,
        )

        class ExampleTable(Structure, Forces):
            custom_column1 = table_column.FloatField()
            custom_column2 = table_column.FloatField()
        ```

        ... would return ...

        ``` python
        ["custom_column1", "custom_column2"]
        ```
        """

        all_columns = cls.get_column_names()
        columns_w_mixin = [
            column for mixin in cls.get_mixins() for column in mixin.get_column_names()
        ]
        extra_columns = [
            column
            for column in all_columns
            if column not in columns_w_mixin and column != "id"
        ]
        return extra_columns

    def write_output_summary(self, directory: Path):
        """
        This writes a "simmate_summary.yaml" file with key output information.
        """

        fields_to_exclude = self.exclude_from_summary + [
            field for mixin in self.get_mixins() for field in mixin.exclude_from_summary
        ]

        all_data = {}
        for column, value in self.__dict__.items():
            if (
                value != None
                and not column.startswith("_")
                and column not in fields_to_exclude
            ):
                all_data[column] = value

        # also add the table name and entry id and website URL
        all_data["_DATABASE_TABLE_"] = self.table_name
        all_data["_TABLE_ID_"] = self.id

        # EXPERIMNETAL: adding workflow URL
        try:
            from simmate.database.base_data_types import Calculation
            from simmate.workflows.utilities import get_workflow

            if isinstance(self, Calculation):
                workflow = get_workflow(self.workflow_name)
                all_data["_WEBSITE_URL_"] = (
                    "http://127.0.0.1:8000/workflows/"  # I assume local host for now
                    f"{workflow.name_type}/{workflow.name_calculator}/"
                    f"{workflow.name_preset}/{self.id}"
                )
        except:
            pass

        summary_filename = directory / "simmate_summary.yaml"
        with summary_filename.open("w") as file:
            content = yaml.dump(all_data)
            file.write(content)

    def to_dict(self):
        return {
            "database_table": self.table_name,
            "database_id": self.id,
        }

    @staticmethod
    def from_dict(source_dict: dict):

        # This method can be return ANY table, so we need to import all of them
        # here. This is a local import to prevent circular import issues.
        from simmate.website.workflows import models as all_datatables

        # start by loading the datbase table, which is given as a module path
        datatable_str = source_dict["database_table"]

        # Import the datatable class -- how this is done depends on if it
        # is from a simmate supplied class or if the user supplied a full
        # path to the class
        # OPTIMIZE: is there a better way to do this?
        if hasattr(all_datatables, datatable_str):
            datatable = getattr(all_datatables, datatable_str)
        else:
            datatable = import_string(datatable_str)

        # These attributes tells us which structure to grab from our datatable.
        # The user should have only provided one -- if they gave more, we just
        # use whichever one comes first.
        run_id = source_dict.get("run_id")
        database_id = source_dict.get("database_id")
        directory = source_dict.get("directory")

        # we must have either a run_id or database_id
        if not run_id and not database_id and not directory:
            raise Exception(
                "You must have either a run_id, database_id, "
                "or directory provided if you want to load a database entry "
                "from a dictionary of metadata."
            )

        # now query the datable with which whichever was provided. Each of these
        # are unique so all three should return a single calculation.
        if database_id:
            database_object = datatable.objects.get(id=database_id)
        elif run_id:
            database_object = datatable.objects.get(run_id=run_id)
        elif directory:
            database_object = datatable.objects.get(directory=directory)

        return database_object

    # -------------------------------------------------------------------------
    # Methods for loading results from files
    # -------------------------------------------------------------------------

    @classmethod
    def from_directory(cls, directory: Path, as_dict: bool = False):
        """
        Loads data from a directory of files
        """

        # check if we have a VASP directory
        vasprun_filename = directory / "vasprun.xml"
        if vasprun_filename.exists():
            return cls.from_vasp_directory(directory, as_dict=as_dict)

        # TODO: add new elif statements when I begin adding new calculators.

        # If we don't detect any directory, we return an empty dictionary.
        # We don't print a warning or error for now because users may want
        # to populate data entirely in python.
        return {} if as_dict else None

    @classmethod
    def from_vasp_directory(cls, directory: Path, as_dict: bool = False):

        from simmate.calculators.vasp.outputs import Vasprun

        vasprun = Vasprun.from_directory(directory)
        return cls.from_vasp_run(vasprun, as_dict=as_dict)

    # -------------------------------------------------------------------------
    # Methods that handle updating a database entry and its related entries
    # -------------------------------------------------------------------------

    def update_from_fields(self, **fields_to_update):
        # go through each key in the dictionary and attach the value to the
        # attribute of this entry
        for key, value in fields_to_update.items():
            setattr(self, key, value)

        # Now we have all data loaded and attached to the database entry, we
        # can call save() to actually update the database
        self.save()

    def update_from_toolkit(self, **fields_to_update):
        """
        Given fundamental "base info" and toolkit objects, this method will
        populate all relevant columns.

        Note, base info also corresponds to the `archive_fieldset`, which
        represents raw data.

        This method is meant for updating existing database entries with new
        data. If your creating a brand-new database entry, use the
        `from_toolkit` method instead.
        """
        fields_expanded = self.from_toolkit(as_dict=True, **fields_to_update)
        self.update_from_fields(**fields_expanded)

    def update_from_directory(self, directory: Path):
        # This is for simple tables. If there are related table entries that
        # need to be created/updated, then this method should be overwritten.
        data_from_dir = self.from_directory(directory, as_dict=True)
        self.update_from_toolkit(**data_from_dir)

    def update_from_results(self, results: dict, directory: Path):
        """
        Updates a database from the results of a workflow run.

        Typically this method is not called directly, as it is used within
        `Workflow._save_to_database` automatically.
        """

        # First update using the results dictionary
        self.update_from_toolkit(directory=str(directory), **results)

        # Many calculations and datatables will have a "from_directory" method
        # that loads data from files. We use this to grab extra fields and
        # add them to our results.
        self.update_from_directory(directory)

    # -------------------------------------------------------------------------
    # Methods that handle updating a database entry and its related entries
    # -------------------------------------------------------------------------

    @classmethod
    def from_toolkit(cls, as_dict: bool = False, **kwargs):
        """
        Given fundamental "raw data" and toolkit objects, this method
        will populate all relevant columns.

        If the table is made up of multiple mix-ins, this method iterates through
        each of the `_from_toolkit` methods of those mixins and combines the results.
        Therefore, you must view this method for each mix-ins to determine which
        kwargs must be passed.

        #### Parameters

        - `as_dict` :
            Whether to return the populated data as a dictionary or to initialize
            it as a database object. Defaults to False.
        - `**kwargs` :
            All fields required in order to initialize the database entry. For
            example, a Structure table would require a toolkit structure, while
            a Thermodynamics table would require an energy.

        Returns
        -------
        a dictionary if as_dict is True; and a database object if as_dict is False
        """

        # Grab a list of all parent classes
        parents = inspect.getmro(cls)

        # As we go through the parent classes below, we will identify the mixins
        # and populate data using those classes. All of this is fed in to our
        # main class at the end of the function. We keep this running dictionary
        # as we go.
        all_data = kwargs.copy()
        # TODO: How should I best handle passing extra kwargs to the final class
        # initialization? For example, I would want to pass `energy` but I wouldn't
        # want to pass the toolkit structure object. I may update this line in
        # the future to remove python objects. For now, I only remove structure
        # and migration_hop because I know that it is a toolkit object -- not
        # a database column.
        all_data.pop("structure", None)
        all_data.pop("migration_hop", None)
        all_data.pop("migration_images", None)
        all_data.pop("band_structure", None)
        all_data.pop("density_of_states", None)

        for parent in parents:

            # Skip the parent class if it doesn't directly inherit from the
            # DatabaseTable class. We do this because we want the fundamental
            # mixins that come with Simmate (such as Structure, Forces, Thermodynamics).
            # We also skip the classes that don't have a _from_toolkit method defined.
            # Right now, this is just the Calculation class that's skipped with this
            # condition.
            if parent.__base__ != DatabaseTable or not hasattr(parent, "_from_toolkit"):
                continue

            # Grab the input arguments for the _from_toolkit method. This will
            # give a list back like... ['cls', 'structure', 'as_dict']. We
            # don't consider as_dict or cls, so we remove those too
            inputs = inspect.getfullargspec(parent._from_toolkit).args
            inputs.remove("as_dict")
            inputs.remove("cls")

            # Now inputs is current of list of keys that we need. Next, we go
            # through our kwargs and see if we have any of these keys, and if so,
            # grab them.
            matching_inputs = {
                key: kwargs[key] for key in inputs if key in kwargs.keys()
            }

            # We now pass these inputs to the _from_toolkit. If we're missing
            # a required input, this will raise an error here. We only
            # want the expanded input, so we request a dictionary, not object.
            data = parent._from_toolkit(**matching_inputs, as_dict=True)

            # Now add this mixin's data to our collective dictionary
            all_data.update(data)

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)

    # -------------------------------------------------------------------------
    # Methods creating new archives
    # -------------------------------------------------------------------------

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
        if cls == DatabaseTable:
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
        return all_fields

    # -------------------------------------------------------------------------
    # Methods that handle loading results from archives
    # -------------------------------------------------------------------------

    # @transaction.atomic  # We can't have an atomic transaction if we use Dask
    @classmethod
    def load_archive(
        cls,
        filename: str | Path = None,
        delete_on_completion: bool = False,
        confirm_override: bool = False,
        parallel: bool = False,
        confirm_sqlite_parallel: bool = False,
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

        - `confirm_override`:
            If the table already has data in it, the user must take particular
            care to downloading new data. This flag makes sure the user has
            made the proper checks to run this action. Default is False.

        - `parallel`:
            Whether to load the data in parallel. If true, this will start
            a local Dask cluster and each data row will be submitted as a task
            to the cluster. This provides substansial speed-ups for loading
            large datasets into the dataset. Default is False.

        - `confirm_sqlite_parallel`:
            If the database backend is sqlite, this parameter ensures the user
            knows what they are doing and know the risks of parallelization.
            Default is False.
        """

        # We disable warnings while loading archives because pymatgen prints
        # a lot of them (for things like rounding or electronegativity alerts).
        warnings.filterwarnings("ignore")

        # make sure the user actually wants to do this!
        cls._confirm_override(
            confirm_override,
            parallel,
            confirm_sqlite_parallel,
        )

        from simmate.toolkit import Structure as ToolkitStructure

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

            # For all entries, convert the structure_string to a toolkit structure
            if "structure_string" in entry:
                structure_str = entry.pop("structure_string")
                structure = ToolkitStructure.from_database_string(structure_str)
                entry["structure"] = structure
            # OPTIMIZE: is there a better way to do decide which entries need to be
            # converted to toolkit objects?

            # BUG: some columns don't properly convert to python objects, but
            # it seems inconsistent when this is done... For now I just manually
            # convert JSON columns
            json_parsing_columns = ["site_forces", "lattice_stress"]
            for column in json_parsing_columns:
                if column in entry:
                    if entry[column]:  # sometimes it has a value of None
                        entry[column] = json.loads(entry[column])
            # OPTIMIZE: consider applying this to the df column for faster loading

            entry_db = cls.from_toolkit(**entry)
            entry_db.save()

        # now iterate through all entries to save them to the database
        if not parallel:
            # If user doesn't want parallelization, we run these in the main
            # thread and monitor progress
            for entry in track(entries):
                load_single_entry(entry)
        # otherwise we use dask to submit these in batches!
        else:

            from simmate.configuration.dask import batch_submit

            batch_submit(
                function=load_single_entry,
                args_list=entries,
                batch_size=15000,
            )

        # We can now delete the files. The zip file is only deleted if requested.
        csv_filename.unlink()
        if delete_on_completion:
            filename.unlink()  # the zip archive

    @classmethod
    def load_remote_archive(
        cls,
        remote_archive_link: str = None,
        confirm_override: bool = False,
        parallel: bool = False,
        confirm_sqlite_parallel: bool = False,
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

        - `confirm_override`:
            If the table already has data in it, the user must take particular
            care to downloading new data. This flag makes sure the user has
            made the proper checks to run this action.

        - `parallel`:
            Whether to load the data in parallel. If true, this will start
            a local Dask cluster and each data row will be submitted as a task
            to the cluster. This provides substansial speed-ups for loading
            large datasets into the dataset. Default is False.

        - `confirm_sqlite_parallel`:
            If the database backend is sqlite, this parameter ensures the user
            knows what they are doing and know the risks of parallelization.
            Default is False.
        """

        # make sure the user actually wants to do this!
        cls._confirm_override(
            confirm_override,
            parallel,
            confirm_sqlite_parallel,
        )

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
        if cls._meta.app_label == "third_parties":
            logging.warning(
                "this data is NOT from the Simmate team, so be sure "
                "to visit the provider's website and to cite their work."
                f" This data is from {cls.source} and the following paper "
                f"should be cited: {cls.source_doi}"
            )

        # Predetermine the file name, which is just the ending of the URL
        archive_filename = remote_archive_link.split("/")[-1]

        # Download the archive zip file from the URL to the current working dir
        logging.info("Downloading archive file...")
        urllib.request.urlretrieve(remote_archive_link, archive_filename)
        logging.info("Done.")

        # now that the archive is downloaded, we can load it into our db
        logging.info("Loading data into Simmate database")
        cls.load_archive(
            archive_filename,
            delete_on_completion=True,
            confirm_override=True,  # we already confirmed this above
            parallel=parallel,
            confirm_sqlite_parallel=True,  # we already confirmed this above
        )
        logging.info("Done.")

    @classmethod
    def _confirm_override(
        cls,
        confirm_override: bool,
        parallel: bool,
        confirm_sqlite_parallel: bool,
    ):
        """
        A utility to make sure the user wants to load new data into their table
        and (if they are using sqlite) that they are aware of the risks of
        parallelizing their loading.

        This utility should not be called directly, as it is used within
        load_archive and load_remote_archive.
        """
        # first check if the table has data in it already. We raise errors
        # to stop the user from doing unneccessary and potentiall destructive
        # downloads
        if cls.objects.exists() and not confirm_override:
            # if the user has a third-party app, we can be more specific with
            # our error message.
            if cls._meta.app_label == "third_parties":
                raise Exception(
                    "It looks like you're using a third-party database table and "
                    "that the table already has data in it! This means you already "
                    "called load_remote_archive and don't need to do it again. "
                    "If you are trying reload a newer version of this data, make "
                    "sure you empty this table first. This can be done by "
                    "reseting your database or manually deleting all objects "
                    "with `ExampleTable.objects.all().delete()`"
                )

            # otherwise warning the user of overwriting data with matching
            # primary keys -- and ask them to use confirm_override.
            raise Exception(
                "It looks like this table already has data in it! By loading an "
                "archive, you could potentially overwrite this data. The most "
                "common mistake is non-unique primary keys between your current "
                "data and the archive -- if there is a duplicate primary key, it "
                "will overwrite your data. If you are confident the data is safe "
                "to load into your database, run this command again with "
                "confirm_override=True."
            )

        # Django and Dask can only handle so much for the parallelization
        # of database writing with SQLite. So if the user has SQLite as their
        # backend, we need to stop them from using this feature.
        from simmate.configuration.django.settings import DATABASES

        if parallel and not confirm_sqlite_parallel and "sqlite3" in str(DATABASES):
            raise Exception(
                "It looks like you are trying to run things in parallel but are "
                "using the default database backend (sqlite3), which is not "
                "always stable for massively parallel methods. You can still "
                "do this, but this message serves as a word of caution. "
                "You If you see error messages pop up saying 'database is "
                "locked', then your database is not stable at the rate you're "
                "trying to write data. This is a sign that you should either "
                "(1) switch to a different database backend such as Postgres "
                "or (2) reduce the parallelization of your tasks. If you are "
                "comfortable with these warnings and know what you're doing, "
                "set confirm_sqlite_parallel=True."
            )

    # -------------------------------------------------------------------------
    # Methods that set up the REST API and filters that can be queried with
    # -------------------------------------------------------------------------

    @classmethod
    @property
    @cache
    def api_filterset(cls) -> django_api_filters.FilterSet:
        """
        Dynamically creates a Django Filter from a Simmate database table.

        For example, this function would take
        `simmate.database.third_parties.MatprojStructure`
        and automatically make the following filter:

        ``` python
        from simmate.website.core_components.filters import (
            DatabaseTableFilter,
            Structure,
            Thermodynamics,
        )


        class MatprojStrucureFilter(
            DatabaseTableFilter,
            Structure,
            Thermodynamics,
        ):
            class Meta:
                model = MatprojStructure  # this is database table
                fields = {...} # this combines the fields from Structure/Thermo mixins

            # These attributes are set using the declared filters from
            # the Structure/Thermo mixins
            declared_filter1 = ...
            declared_filter1 = ...
        ```
        """

        # ---------------------------------------------------------------------
        # This is the filter mix-in for the base DatabaseTable class, which
        # ALL other filters will use. We set this up manually.
        # TODO: Consider moving this outside of this method.
        class ApiFilter(django_api_filters.FilterSet):
            class Meta:
                table = DatabaseTable
                fields = dict(
                    # id=["exact"],  --> automatically added...?
                    created_at=["range"],
                    updated_at=["range"],
                )

            def skip_filter(self, queryset, name, value):
                """
                For filter fields that use this method, nothing is done to queryset. This
                is because the filter is typically used within another field. For example,
                the `include_subsystems` field is not applied to the queryset, but it
                is used within the `filter_chemical_system` method.
                """
                return queryset

        # ---------------------------------------------------------------------

        # If calling this method on the base class, just return the sole mix-in.
        if cls == DatabaseTable:
            return ApiFilter

        # First we need to grab the parent mixin classes of the table. For example,
        # the MatprojStructure uses the database mixins ['Structure', 'Thermodynamics']
        # while MatprojStaticEnergy uses ["StaticEnergy"].
        table_mixins = cls.get_mixins()

        # When we make this filter, we want it to inherit from the filters of
        # all mixins available. We therefore grab all these filters into a list.
        # We also add the standard ModelForm class from django-filters.
        filter_mixins = [ApiFilter]
        filter_mixins += [mixin.api_filterset for mixin in table_mixins]

        # "Declared Filters" are ones normally set as an attribute when creating
        # a Django filter, whereas normal filters are provided in a meta. For
        # example...
        #
        # class Structure(filters.FilterSet):
        #     class Meta:
        #         model = StructureTable
        #         fields = dict(
        #             nsites=["range"],  <-------------- field filter
        #             nelements=["range"],  <----------- field filter
        #         )
        #     include_subsystems = filters.BooleanFilter(
        #         field_name="include_subsystems",
        #         label="Include chemical subsystems in results?",
        #         method="skip_filter",
        #     ) <-------------------------------------- declared filter
        #     chemical_system = filters.CharFilter(
        #         method="filter_chemical_system"
        #     ) <-------------------------------------- declared filter
        #
        # I need to separate these out in order to create our class properly
        field_filters = {}
        declared_filters = {}
        filter_methods = {}
        for field, conditions in cls.api_filters.items():
            if isinstance(conditions, django_api_filters.Filter):
                declared_filters.update({field: conditions})
                # For the declared filters, there is sometimes a method that
                # needs to be called. This will be attached to the original
                # mixin as a method of the same name. Here we check if there
                # is a method and attach it. For an example of this, see the
                # "filter_chemical_system" method of the Structure class.
                if conditions.method and conditions.method != "skip_filter":
                    filter_methods.update(
                        {conditions.method: getattr(cls, conditions.method)}
                    )
            else:
                field_filters.update({field: conditions})

        # combine the fields of each filter mixin. Note we use .get_fields instead
        # of .fields to ensure we get a dictionary back
        field_filters.update(
            {
                field: conditions
                for mixin in filter_mixins
                for field, conditions in mixin.get_fields().items()
            }
        )

        # Also combine all declared filters from each mixin
        declared_filters.update(
            {
                name: filter_obj
                for mixin in filter_mixins
                for name, filter_obj in mixin.declared_filters.items()
            }
        )

        # The FilterSet class requires that we set extra fields in the Meta class.
        # We define those here. Note, we accept all fields by default and the
        # excluded fields are only those defined by the supported form_mixins -
        # and we skip the first mixin (which is always DatabaseTableFilter)
        class Meta:
            model = cls
            fields = field_filters

        extra_attributes = {"Meta": Meta, **declared_filters, **filter_methods}
        # BUG: __module__ may need to be set in the future, but we never import
        # these forms elsewhere, so there's no need to set it now.

        # Now we dynamically create a new form class that we can return.
        NewClass = type(cls.table_name, tuple(filter_mixins), extra_attributes)

        # Match the filter name to the table name
        NewClass.filter_name = cls.table_name

        return NewClass

    @classmethod
    @property
    @cache
    def api_filters_extra(cls):
        """
        Finds all columns that aren't covered by the supported Form mix-ins.

        For example, a form made from the database table...

        ``` python
        from simmate.database.base_data_types import (
            table_column,
            Structure,
            Forces,
        )

        class ExampleTable(Structure, Forces):
            custom_column1 = table_column.FloatField()
            custom_column2 = table_column.FloatField()
        ```

        ... would return ...

        ``` python
        ["custom_column1", "custom_column2"]
        ```
        """

        all_columns = cls.api_filterset.base_filters.keys()
        columns_w_mixin = [
            column
            for mixin in cls.get_mixins()
            for column in mixin.api_filterset.base_filters.keys()
        ]
        extra_columns = [
            column
            for column in all_columns
            if column not in columns_w_mixin and column != "id"
        ]
        return extra_columns
