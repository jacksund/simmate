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
import textwrap
import urllib
import warnings
from functools import cache
from pathlib import Path

import pandas
import yaml
from django.apps import apps
from django.core.paginator import Page, Paginator
from django.db import models  # see comment below
from django.db import models as table_column
from django.forms.models import model_to_dict
from django.http import HttpRequest, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.urls import resolve, reverse
from django.utils.module_loading import import_string
from django.utils.timezone import datetime, now, timedelta
from rich.progress import track

from simmate.configuration import settings
from simmate.database.utilities import check_db_conn
from simmate.utilities import chunk_list, get_attributes_doc

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
        columns: list[str] = (),
        exclude_columns: list[str] = (),
        limit: int = None,
        use_cache: bool = True,
    ) -> pandas.DataFrame:
        """
        Returns a Pandas DataFrame of the search results

        Paramaters
        -----------
        - `columns`:
            The model field names (columns) to utilise in creating the DataFrame.
            You can span a relationships in the usual Django ORM way by using
            the foreign key field name separated by double underscores and refer
            to a field in a related model.
        - `exclude_columns`:
            If columns is left as None (meaning use all cols), this is the
            list of cols that will be ignored from the full default list.
        - `limit`:
            whether to limit the total number of rows. This is the equivalent
            of `.all()[:limit].to_dataframe()`
        - `use_cache`:
            whether to use django's result cache if the query has been executed
            already
        """

        # This method originally used `django_pandas` but we since decided to
        # implement our own method that is optimized for our own use cases and avoids
        # cases where the queryset is accidentally ran twice:
        # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/
        # https://github.com/chrisdev/django-pandas/issues/138

        if not columns:
            has_user_cols = False
            # TODO: I'd like to include foreign keys or other relations by default
            columns = [
                c
                for c in self.model.get_column_names(include_relations=False)
                if c not in exclude_columns
            ]
        else:
            has_user_cols = True

        values_list = None  # set dynamically

        # check if the query has been executed already. If so, we use those cached
        # results to get our values_list. (unless the query gave back an
        # incomplete values_list)
        if use_cache and self._result_cache is not None:

            # check if we have a list of models or values
            if self._iterable_class == models.query.ValuesListIterable:

                # if the user has a `values_list` call to the queryset, and didn't
                # set columns for `to_dataframe`, we'll use those cols for the df
                if not has_user_cols:
                    columns = list(self._fields)
                    values_list = list(self)

                # otherwise, we need to make sure that we have all the values
                # needed for the dataframe If not, another query is needed
                else:
                    cache_columns = list(self._fields)
                    has_all_cols = all([c in cache_columns for c in columns])
                    if has_all_cols:
                        i_map = [cache_columns.index(c) for c in columns]
                        values_list = [
                            tuple([entry[i] for i in i_map]) for entry in self
                        ]
                    # else:
                    #     logging.warning(
                    #         "Cached values list is incompatible with the requested "
                    #         "dataframe columns list. A new db query will be ran "
                    #         "to fix this. "
                    #     )
                    #     # we leave values_list=None so we get new query below

            # otherwise we have a list of models. We'll have to trust that
            # the user properly used `select_related` and `only` ahead of time.
            # Optimization falls on them since the query was already executed
            else:
                # logging.warning(
                #     "You are using the query cache to generate a dataframe. "
                #     "Make sure you used `select_related` and `only` on your queryset "
                #     "to properly optimize your query. Otherwise this next call "
                #     "will be extremely slow: "
                # )
                values_list = [
                    tuple([getattr(entry, col) for col in columns]) for entry in self
                ]

            # limit if it was requested
            if values_list and limit:
                values_list = values_list[:limit]

        # if the query hasn't been ran yet, we can make sure we run an optimized
        # query -- one were we only grab the relevent columns and skip object
        # generation
        if not values_list:
            query = (
                self.values_list(*columns)
                if not limit
                else self.values_list(*columns)[:limit]
            )
            values_list = list(query)

        df = pandas.DataFrame.from_records(
            data=values_list,
            columns=columns,
        )

        # TODO: change choice fields to verbose
        # TODO: add toolkit col

        return df

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

        # now convert these objects to a pandas dataframe, using just
        # the archive columns that are being stored
        df = self.to_dataframe(columns=self.model.archive_fieldset)

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

    # -------------------------------------------------------------------------

    def to_api_dict(
        self, next_url: str = None, previous_url: str = None, **kwargs
    ) -> dict:
        """
        Converts the search results to a API dictionary. This is used to generate
        the default API response and can be overwritten.

        Note, this is typically called on the *page* object list, and not the
        full query results.
        """
        # We follow the list api format that django rest_framework uses. The
        # next/previous is for pagination
        return {
            # OPTIMIZE: counting can take ~20 sec for ~10 mil rows, which is
            # terrible for a web UI. I tried a series of fixes but no luck:
            #   https://stackoverflow.com/questions/55018986/
            "count": self.count(),
            "next": next_url,
            "previous": previous_url,
            "results": [entry.to_api_dict(**kwargs) for entry in self.all()],
        }

    def to_json_response(self, **kwargs) -> JsonResponse:
        """
        Takes the API dictionary (from `to_api_dict`) and converts it to a
        Django JSON reponse
        """
        return JsonResponse(self.to_api_dict(**kwargs))

    # -------------------------------------------------------------------------

    def filter_by_tags(self, tags: list[str]):
        """
        A utility filter() method that helps query the 'tags' column of a table.

        NOTE: Pay close attention to filtering when using the SQLite3 backend
        as Django warns about unexpected substring matching:
            https://docs.djangoproject.com/en/4.2/ref/databases/#substring-matching-and-case-sensitivity
        """

        if tags:
            new_query = self
            for tag in tags:
                if settings.database_backend == "postgresql":
                    new_query = new_query.filter(tags__contains=tag)
                elif settings.database_backend == "sqlite3":
                    new_query = new_query.filter(tags__icontains=tag)
        else:
            new_query = self.filter(tags=[])

        return new_query

    # -------------------------------------------------------------------------

    # These methods behaves exactly the save as django's default ones, but they
    # are wrapped to catch errors such as "connection closed" failures
    # and retries with a new connection.

    @check_db_conn
    def bulk_create(self, *args, **kwargs):
        return super().bulk_create(*args, **kwargs)

    @check_db_conn
    def bulk_update(self, *args, **kwargs):
        return super().bulk_update(*args, **kwargs)

    # -------------------------------------------------------------------------

    # Misc utilities for common tasks

    def filter_age(self, cutoff: str, age_column: str = "created_at"):
        """
        A convienience filter for date-based filters such as "created in the
        last 24hrs". Uses the `created_at` column by default but can be
        pointed to any datetime column.

        Options for `cutoff` are 'hour', 'day', 'week', 'month', and 'year'
        """
        current_time = now()
        if cutoff == "hour":
            cutoff_date = current_time - timedelta(hours=1)
        elif cutoff == "day":
            cutoff_date = current_time - timedelta(days=1)
        elif cutoff == "week":
            cutoff_date = current_time - timedelta(days=7)
        elif cutoff == "month":
            cutoff_date = current_time - timedelta(days=30)
        elif cutoff == "year":
            cutoff_date = current_time - timedelta(days=365)
        else:
            raise Exception(f"Unknown age cutoff: {cutoff}")

        return self.filter(**{f"{age_column}__gte": cutoff_date})

    def count_by_column(self, column: str) -> dict:
        """
        Util to count the rows per column. Meant for ChoiceField columns such
        as "status" where you want to know how many of each there are.
        """
        result = self.values(column).annotate(count=table_column.Count(column))
        return {entry[column]: entry["count"] for entry in result}


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

    id = table_column.AutoField(primary_key=True)
    """
    The unique ID number assigned to each entry.
    """

    created_at = table_column.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        db_index=True,
    )
    """
    Timestamp of when this row was first added to the database table
    """

    updated_at = table_column.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
        db_index=True,
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
    tables (such as those from a third-party database) this is value
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

    external_website: str = None
    """
    The homepage of the source website, if the data is loaded from a third-party
    """

    remote_archive_link: str = None
    """
    The URL that is used to download the archive and then populate this table.
    Many tables have pre-existing data that you can download and load into 
    your local database, so if this attribute is set, you can use the 
    `load_remote_archive` method.
    """

    # I override the default manager with the one we define above, which has
    # extra methods useful for our querysets.
    objects = DatabaseTableManager()
    """
    Accesses all of the rows in this datatable and initiates a SearchResults
    object. Using this, you can perform complex filtering and conversions on
    data from this table.
    """
    # TODO: switch to...
    # https://docs.djangoproject.com/en/5.0/topics/db/managers/#creating-a-manager-with-queryset-methods
    # objects = SearchResults.as_manager()

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

    exclude_from_summary: list[str] = []
    """
    When writing output summaries, these columns will be ignored. This is useful
    if you have a column for storing raw data that isn't friendly to read in
    the yaml format. 'structure' is an example of a field we'd want to
    exclude because its not very readable and is available elsewhere.
    """

    workflow_columns: dict = {}
    """
    WARNING: advanced users only (this is still in early testing)
    
    When subclassing DatabaseTable, you may want to add a column that is 
    populated via a specific workflow (e.g. a quick property calculation). This
    attribute defines the mapping of a new column to a workflow name.
    
    You must define the column separately (as dynamically adding columns is not
    possible with Django models) and the workflow must be accessible with
    the `get_workflow` utility.
    
    Note, this is meant for bringing workflow results IN TO a table -- like
    having a full dataset (like the OQMD library) and wanting to add a column
    for some ML/AI model you've built. If your workflow takes >30s per entry,
    it is often better to build a separate workflow table to store results there.
    """

    # -------------------------------------------------------------------------
    # The primary save methods used to add entries to the database
    # -------------------------------------------------------------------------

    # These methods behaves exactly the save as django's default ones, but they
    # are wrapped to catch errors such as "connection closed" failures
    # and retries with a new connection.

    @check_db_conn
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
    @property
    def columns(cls):
        return cls._meta.get_fields()

    @classmethod
    def get_column_names(
        cls,
        include_relations: bool = True,
        include_parents: bool = True,
    ) -> list[str]:
        """
        Returns a list of all the column names for this table and indicates which
        columns are related to other tables. This is primarily used to help
        view what data is available.
        """
        return [
            column.name
            for column in cls._meta.get_fields(include_parents)
            if include_relations or not column.is_relation
        ]

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
            (
                # BUG: use __name__ instead of table_name to account for tables
                # that only inherit from Django models (e.g. User model)
                column.name + f" (relation to {column.related_model.__name__})"
                if column.is_relation
                else column.name
            )
            for column in cls._meta.get_fields()
        ]

        # Then use yaml to make the printout pretty (no quotes and separate lines)
        print(yaml.dump(column_names))

    @classmethod
    def get_column_docs(cls) -> dict:
        """
        Gives all column names as well as their docstring descriptions
        """

        # OPTIMIZE: this is slow and should be cached. Or even use a more
        # standard method approach like django's `help_text`.
        # We opted for using attribute docstrings, which actually aren't
        # officially supported by python and involve inspecting the source
        # code file.

        all_attr_docs = get_attributes_doc(cls)

        column_docs = {
            name: descr
            for name, descr in all_attr_docs.items()
            if name in cls.get_column_names()
        }

        return column_docs

    @classmethod
    def get_table_docs(cls) -> dict:
        """
        Grabs table metadata and column descriptions into a single dictionary
        """

        # !!! source is kinda the verbose name for third-party
        # data, but I should standardize how user-friendly names are set.
        name = cls.source if isinstance(cls.source, str) else cls.table_name

        return {
            "name": name,
            "table_info": {
                "sql_name": cls._meta.db_table,
                "python_name": cls.table_name,
                "python_path": cls.__module__,
                "website_url": cls.url_table,
            },
            "table_description": textwrap.dedent(cls.__doc__).strip(),
            "column_descriptions": cls.get_column_docs(),
        }

    @classmethod
    def show_table_docs(cls, print_out: bool = True) -> str:
        """
        Prints all docs about this table. While a GUI is much better for exploring
        table docs, this method is more useful for outputting text that LLM
        chatbots can use.
        """
        # OPTIMIZE: still need to figure out what format works best with chatbots

        docs = cls.get_table_docs()

        # we build the string before printing anything out
        final_str = ""

        final_str += f"# {docs['name']}\n\n"

        final_str += (
            "## About\n\n"
            f"\t- Python Class Name: {docs['table_info']['python_name']}\n"
            f"\t- Python Import Path: {docs['table_info']['python_path']}\n"
            f"\t- SQL Table Name: {docs['table_info']['sql_name']}\n"
            f"\t- Website UI Location: {docs['table_info']['website_url']}\n\n"
        )

        final_str += "## Table Description\n\n" f"{docs['table_description']}\n\n"

        final_str += "## Column Descriptions\n\n"
        for col_name, col_descr in docs["column_descriptions"].items():
            final_str += f"### `{col_name}`\n{col_descr}\n\n"

        if print_out:
            print(final_str)
        else:
            return final_str

    @classmethod
    def get_mixins(cls) -> list:  # -> List[DatabaseTable]
        """
        Grabs the mix-in Tables that were used to make this class. This will
        be mix-ins like Structure, Forces, etc.

        These are typically all from the `simmate.database.base_data_types`
        module. Custom mix-ins can be provided
        """
        return [
            parent
            for parent in cls.__bases__
            if issubclass(parent, DatabaseTable) and parent != DatabaseTable
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
                    f"{workflow.name_type}/{workflow.name_app}/"
                    f"{workflow.name_preset}/{self.id}"
                )
                # OPTIMIZE: what if I switch database results to be queried
                # in the Data tab rather than for each workflow:
                # all_data["_WEBSITE_URL_"] = self.url
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

    @classmethod
    def from_dict(cls, source_dict: dict):
        # start by loading the datbase table, which is given as a module path
        table_name = source_dict["database_table"]
        datatable = cls.get_table(table_name)

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

    @classmethod
    def from_dicts(cls, source_dicts: list[dict]):
        """
        Given many database dictionaries, this will perform optimized database
        queries.

        This method should be preffered over from_dict when you have a many
        entries that you want to load
        """
        # collect the unique sources so that we can make a single query.
        query_info = {}  # dictionary of database table + all ids
        for source in source_dicts:
            table_name = source["database_table"]
            table_id = source["database_id"]

            if table_name not in query_info.keys():
                query_info[table_name] = []

            query_info[table_name].append(table_id)

        results = []
        for table_name, table_ids in query_info.items():
            datatable = cls.get_table(table_name)
            query = datatable.objects.filter(id__in=table_ids).all()
            results += list(query)

        # the query does not return the ids in the same order that table_ids
        # was given. Order is important in some cases, so we fix this here.
        all_data_dict = {entry.id: entry for entry in results}
        all_data_ordered = [
            all_data_dict[id]
            for id in table_ids
            if id in all_data_dict.keys()  # BUG: should I warn if the id isn't found?
        ]

        return all_data_ordered

    @staticmethod
    def get_table(table_name: str):  # returns subclass of DatabaseTable
        """
        Given a table name (e.g. "MaterialsProjectStructure") or a full import
        path of a table, this will load and return the corresponding table class.
        """

        # "." in the name indicates an import path
        if "." in table_name:
            datatable = import_string(table_name)

        # otherwise search all tables and see if there is a *single* match
        else:
            all_models = apps.get_models()
            matches = []
            for model in all_models:
                if hasattr(model, "table_name") and model.table_name == table_name:
                    matches.append(model)
            if len(matches) == 1:
                datatable = matches[0]
            elif len(matches) > 1:
                raise Exception(
                    f"More than one table has the name {table_name}."
                    "Provide a full path to ensure the correct table is returned"
                )
            elif len(matches) == 0:
                raise Exception(f"Unable to find database table with name {table_name}")

        return datatable

    # -------------------------------------------------------------------------
    # Methods for loading results from files
    # -------------------------------------------------------------------------

    @classmethod
    def from_directory(cls, directory: Path, as_dict: bool = False):
        """
        Loads data from a directory of files
        """
        # If any of these files are present, then we immediately know which
        # program was used to write the output files
        vasprun_filename = directory / "vasprun.xml"
        pwscf_filename = directory / "pwscf.xml"

        # check if we have a VASP directory
        if vasprun_filename.exists():
            return cls.from_vasp_directory(directory, as_dict=as_dict)

        # check if we have a Quantum Espresso (PWscf) directory
        elif pwscf_filename.exists():
            return cls.from_pwscf_directory(directory, as_dict=as_dict)

        # TODO: add new elif statements when I begin adding other new apps.

        # If we don't detect any directory, we return an empty dictionary.
        # We don't print a warning or error for now because users may want
        # to populate data entirely in python.
        return {} if as_dict else None

    @classmethod
    def from_vasp_directory(cls, directory: Path, as_dict: bool = False):
        from simmate.apps.vasp.outputs import Vasprun

        vasprun = Vasprun.from_directory(directory)
        return cls.from_vasp_run(vasprun, as_dict=as_dict)

    @classmethod
    def from_pwscf_directory(cls, directory: Path, as_dict: bool = False):
        from simmate.apps.quantum_espresso.outputs import PwscfXml

        pwscf_run = PwscfXml.from_directory(directory)
        return cls.from_pwscf_run(pwscf_run, as_dict=as_dict)

    # -------------------------------------------------------------------------
    # Methods that handle updating a database entry and its related entries
    # -------------------------------------------------------------------------

    def update_wo_timestamp(self, **kwargs):
        """
        Saves changes to the database WITHOUT affecting the `updated_at` or any
        other "auto_now=True" columns. IF the table has a `history` table, this
        will also be skipped.

        This is effectively a hack and can mean the `updated_at` columns becomes
        misleading to users, so use sparingly!! It is intended for frequently
        cached calculated columns. For example, a column that is `status_age`
        that is updated daily (even when nothing else has change)

        Note, the object that this is called on will be out of date once called.
        You should requery the database to get the updated entry.
        """
        self.__class__.objects.filter(id=self.id).update(**kwargs)

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
        all_data.pop("molecule", None)

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

            from simmate.configuration.dask import batch_submit

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
        if cls._meta.app_label == "data_explorer":
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
            if cls._meta.app_label in [
                "aflow",
                "cod",
                "jarvis",
                "materials_project",
                "oqmd",
            ]:
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
                "archive, you could potentially overwrite this data. Make sure "
                "common mistake that you have unique primary keys between your current "
                "data and the archive -- if there is a duplicate primary key, it "
                "will overwrite your data. If you are confident the data is safe "
                "to load into your database, run this command again with "
                "confirm_override=True."
            )

        # Django and Dask can only handle so much for the parallelization
        # of database writing with SQLite. So if the user has SQLite as their
        # backend, we need to stop them from using this feature.
        if (
            parallel
            and not confirm_sqlite_parallel
            and "sqlite3" in str(settings.database_backend)
        ):
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

    # !!! DEV -- This section is currently a mixture of depreciated and experimental
    # methods. Users should avoid until these methods become stable

    @classmethod
    def get_web_queryset(cls):
        """
        Optional method to override the input queryset which modify how
        `filter_from_request` queries data. By default it return the full
        `cls.objects` queryset.

        This can is useful when you either need to (1) prevent certain data
        from being accessible in the UI, and (2) optimize the input queryset
        using `select_related(...)` or `prefetch_related(...)` calls.
        """
        return cls.objects

    # SINGLE OBJECT APIs

    def to_api_dict(self, fields: list[str] = None, exclude: list[str] = None) -> dict:
        """
        Converts a single instance (row) of this database table to a API dictionary.
        This is used to generate the default API response and can be overwritten.
        """
        # See https://stackoverflow.com/questions/21925671/
        # Consider forking model_to_dict or writing custom method.
        # !!! Does not support columns accross relations such as "user__email"
        return model_to_dict(
            instance=self,
            fields=self.get_column_names() if fields is None else fields,
            exclude=exclude,
        )

    def to_json_response(self, **kwargs) -> JsonResponse:
        """
        Takes the API dictionary (from `to_api_dict`) and converts it to a
        Django JSON reponse
        """
        return JsonResponse(self.to_api_dict(**kwargs))

    @classmethod
    def get_json_response(cls, pk) -> JsonResponse:
        """
        Given the object id, will query and return the JSON response. This will
        also give a 404 response if it is not found
        """
        obj = get_object_or_404(cls, pk=pk)
        return obj.to_json_response()

    # MULTI OBJECT APIs

    # max_api_count: int = 10_000
    # NOTE: counting the total number of results in a query is MUCH
    # slower than just loading a single page! See...
    #   https://wiki.postgresql.org/wiki/Slow_Counting
    # To address this, we limit the maximum queryset size to be 10k. This
    # is a large number because counting queries really only becomes an
    # issue with >1mil rows in the dataset.
    # We still allow users to set "None" disable this feature.

    @classmethod
    @property
    @cache
    def filter_methods(cls) -> list[str]:
        """
        All filtering methods that can be used to narrow a queryset
        """
        excluded_methods = [
            "filter_from_config",
            "filter_from_request",
            "filter_methods",
            "filter_methods_extra_args",
        ]
        return [
            method
            for method in dir(cls.objects)
            if method.startswith("filter_") and method not in excluded_methods
        ]  # dir() looks to be faster than inspect.getmembers

    @classmethod
    @property
    @cache
    def filter_methods_extra_args(cls) -> list[str]:
        """
        Any unique parameters that are used as kwargs in `filter_methods`
        """
        column_names = cls.get_column_names()
        extra_args = []
        for method in cls.filter_methods:
            sig = inspect.signature(getattr(cls.objects, method))
            for parameter in list(sig.parameters):
                if parameter not in column_names and parameter not in [
                    "self",
                    "kwargs",
                ]:
                    extra_args.append(parameter)
        return extra_args

    @classmethod
    def filter_from_url(cls, url: str, **kwargs) -> SearchResults | Page:
        """
        Given the full URL of a Simmate REST API endpoint (in the /data section),
        this will return the queryset. This method can be used on the base
        DataTable class (where it loads the proper table for you) or on a
        subclass (where it validates that you're using the correct subclass).
        """

        url = urllib.parse.urlparse(url)

        # make sure the base URL is the simmate website
        if settings.website.debug == False and "simmate." not in url.netloc:
            raise Exception("This is not a Simmate website url")

        # convert the URL into a request object
        request = HttpRequest()
        request.path = url.path
        request.GET = QueryDict(url.query)
        request.resolver_match = resolve(url.path)

        # make sure we are looking at a /data view in tables
        if not (
            request.resolver_match.namespaces[0] == "data_explorer"
            and request.resolver_match.url_name == "table"
        ):
            raise Exception("This is not a Simmate `data_explorer.table` url")

        # grab the appropriate table
        table_name = request.resolver_match.kwargs["table_name"]
        expected_table = cls.get_table(table_name)

        if cls != DatabaseTable and cls != expected_table:
            raise Exception(
                "The table indicated in the URL does not match the table class you are using. "
                f"current table: {cls} ;  url table: {expected_table}"
            )

        return expected_table.filter_from_request(
            request=request,
            **kwargs,
        )

    @classmethod
    def filter_from_request(
        cls,
        request: HttpRequest,
        paginate: bool = True,
    ) -> SearchResults | Page:
        """
        Generates a filtered queryset from a django HttpRequest using the
        request's GET parameters
        """
        # In the past, this was handled by the django-filter package, but this
        # became too verbose and tedious. You'd need to list out "gt", "gte", and
        # any other field lookups allowed for EACH field... In practice, we want
        # to just allow anything and trust the user follows the docs correctly.
        from simmate.website.utilities import parse_request_get

        get_kwargs = parse_request_get(
            request,
            include_format=False,
            group_filters=True,
        )
        return cls.filter_from_config(
            **get_kwargs,
            paginate=paginate,
            use_web_queryset=True,
        )

    @classmethod
    def filter_from_config(
        cls,
        filters: dict,
        # True default is "id" when pagination is needed. Using "None" respects
        # if there is ordering from any of the filters (e.g. filter_similarity_2d)
        order_by: str | list[str] = None,  # could be "id" or ["created_at", "id", ...]
        limit: int = 10_000,
        page: int = 1,
        page_size: int = 25,
        paginate: bool = True,
        use_web_queryset: bool = False,
    ) -> SearchResults | Page:
        """
        Converts URL kwargs into a queryset.
        """

        # Some tables have "advanced" filtering logic. These want us to call
        # a filtering method, rather than just passing the kwarg to `objects.filter()`.
        # An example of this would be "chemical_system" for Structure, which
        # needs to (a) clean the query by converting to the element order that
        # db uses, and (b) base its filtering logic on other kwargs like
        # "include_subsystems".
        basic_filters = {}
        filter_methods = cls.filter_methods
        filter_methods_args = cls.filter_methods_extra_args

        queryset = cls.objects if not use_web_queryset else cls.get_web_queryset()
        for filter_name, filter_value in filters.items():

            # if we have a filter method, we apply it to our queryset right away
            if f"filter_{filter_name}" in filter_methods:
                # The args can be given one of two ways:
                #   1. a single arg
                #   2. kwargs (a json dict with key-values)
                # Here are examples for each approach to call the
                # method `filter_age(cutoff, age_column)`, where 'cutoff' is
                # required while age_column is an optional input
                #   age="day"
                #   age={"cutoff": "day", "age_column": "updated_at"}
                # The latter is more explicit and robust to errors.
                # BUG: if the first positional is supposed to be a dict,
                # you must use the JSON approach instead.
                method = getattr(queryset, f"filter_{filter_name}")
                if not isinstance(filter_value, dict):
                    queryset = method(filter_value)
                else:
                    queryset = method(**filter_value)

            # these are kwargs only needed in filter methods (e.g. `include_subsystems`)
            elif filter_name in filter_methods_args:
                continue  # these are only used via method_kwargs above

            # otherwise we have a basic filter (e.g. `user__email__startswith`)
            else:
                basic_filters[filter_name] = filter_value

        # now that all filter_methods have been applied, we now apply basic ones
        queryset = queryset.filter(**basic_filters)

        # Handle ordering
        # the ordered_by kwarg takes priority, but in cases where none is set
        # AND the queryset filters didn't give any, pagination still requires
        # that we do some form of ordering, so we filter by id in reverse
        if paginate and not order_by and not queryset.query.order_by:
            order_by = "-id"
        if order_by:
            # in case only a single str was given, convert to list
            if isinstance(order_by, str):
                order_by = [order_by]
            queryset = queryset.order_by(*order_by)

        if limit:
            queryset = queryset[:limit]

        # if requested, split the results into pages and grab the requested one
        if paginate:
            paginator = Paginator(object_list=queryset, per_page=page_size)
            page_obj = paginator.get_page(number=page)
            return page_obj
        else:
            return queryset

    # -------------------------------------------------------------------------
    # Methods that link to the website UI
    # -------------------------------------------------------------------------

    # experimental overrides for templates used by the Data Explorer app

    html_display_name: str = None
    html_description_short: str = None
    html_tabtitle_label_col: str = "id"

    html_about_template: str = "data_explorer/table_about.html"
    html_table_template: str = "data_explorer/table.html"
    html_entry_template: str = "data_explorer/table_entry.html"
    html_entries_template: str = "data_explorer/table_entries.html"

    # This take the views below and just put them within the main body
    html_search_template: str = "core_components/unicorn_full_page.html"
    html_entry_form_template: str = "core_components/unicorn_full_page.html"

    # Unicorn views (side panels in the table view of the Data Explorer app)
    html_form_view: str = None
    html_enabled_forms: list[str] = []
    # options: "search", "create", "update", "create_many", "create_many_entry", "update_many"

    @property
    def html_tabtitle_label(self) -> str:
        """
        Provides a label to put in the tab title. By default, this uses the id
        """
        return str(getattr(self, self.html_tabtitle_label_col))

    @classmethod
    @property
    def url_table(self) -> str:
        """
        Provides the URL link to the database table page in the Simmate website
        """
        # "http://127.0.0.1:8000"  # TODO: have env variable for host name?
        return f"/data/{self.table_name}"

    @property
    def url(self) -> str:
        """
        Provides the URL link to the database entry page in the Simmate website
        """
        return f"{self.url_table}/{self.id}"

    def get_absolute_url(self):
        """
        Provides the full URL link to the database entry page in the Simmate website.

        This is for use in template views, whereas user may find the `url`
        property easier to work with
        """
        return reverse(
            "data_explorer:table-entry",
            kwargs={"table_name": self.table_name, "table_entry_id": self.pk},
        )

    @classmethod
    @property
    def html_extra_table_context(cls) -> dict:
        return {}

    @property
    def html_extra_entry_context(self) -> dict:
        return {}

    # -------------------------------------------------------------------------
    # Methods for reports and plotting.
    # -------------------------------------------------------------------------

    # Note, many methods associated with this section would normally be
    # attached to custom QuerySet/SearchResults subclasses, but that leads
    # to extra boiler plate.

    enable_html_report: bool = False
    report_df_columns: list[str] = None

    @classmethod
    def get_report(cls, data_source: SearchResults | Page = None) -> dict:
        """
        Gives a dictionary of report information, such as statistical values
        or plotly figures.

        If data_source is left as None, the entire table is used
        """

        # convert to a SearchResults/queryset obj
        if data_source == None:
            data_source = cls.objects  # use full table by default
        elif isinstance(data_source, SearchResults):
            pass  # queryset ready to go
        elif isinstance(data_source, Page):
            data_source = data_source.paginator.object_list

        df = data_source.to_dataframe(cls.report_df_columns)
        return cls.get_report_from_df(df)

    @classmethod
    def get_report_from_df(cls, df: pandas.DataFrame) -> dict:
        raise NotImplementedError("A `get_report_from_df` method must be provided")

    # -------------------------------------------------------------------------
    # Methods that populate "workflow columns" of custom tables
    # -------------------------------------------------------------------------

    @classmethod
    def populate_workflow_column(
        cls,
        column_name: str,
        batch_size: int = 500,
        update_only: bool = True,
    ):
        """
        Populates a specific workflow column. The column must be present in the
        `workflow_columns` attribute.
        """

        # BUG: using 'id__in' below might cause batches >1k to fail
        if batch_size > 1000:
            logging.info(
                "This method uses a 'IN' clause to select batches of IDs, so "
                "batches larger than 1k can cause performance issues and errors."
            )

        # local import to avoid circular dependency
        from simmate.workflows.utilities import get_workflow

        # grab the workflow mapped to this column
        workflow_name = cls.workflow_columns[column_name]
        workflow = get_workflow(workflow_name)

        # BUG: I assume inputs are the common ones for now...
        # but I need a way to specify this for more diverse workflows
        # (I give one suggested fix to this in the while-loop below)
        if "molecules" not in workflow.parameter_names:
            raise Exception(
                "We are still at early stage testing for this method, so "
                "it only supports workflows that take 'molecules' as an "
                "input parameter. Reach out to our team if you'd like "
                "us to add additional support."
            )

        filters = {f"{column_name}__isnull": True} if update_only else {}
        ids_to_update = cls.objects.filter(**filters).values_list("id", flat=True).all()

        logging.info(
            f"Updating '{column_name}' column using '{workflow_name}' "
            f"for {len(ids_to_update)} entries"
        )
        for ids_chunk in chunk_list(ids_to_update, batch_size):
            try:
                # grab the next set of objects to update
                objs_to_update = cls.objects.filter(id__in=ids_chunk).all()

                # First check for a user-defined method.
                predefined_method = f"_format_inputs_for__{column_name}"
                if hasattr(cls, predefined_method):
                    # method = getattr(cls, predefined_method)
                    # method(workflow, objs_to_update)
                    raise NotImplementedError("This feature is still being developed")
                else:
                    # OPTIMIZE: should I support run_cloud for parallelization?
                    # BUG: see comment at start of for-loop where I say I assume
                    # a 'molecules' input
                    status = workflow.run(
                        molecules=objs_to_update.to_toolkit(),
                        compress_output=True,
                    )
                    results = status.result()
                    logging.info("Saving results to db")

                    # update the column with the new value and save
                    for entry, entry_result in zip(objs_to_update, results):
                        setattr(entry, column_name, entry_result)
                    cls.objects.bulk_update(objs_to_update, [column_name])
            except:
                logging.warning("BATCH FAILED")
                continue

    @classmethod
    def populate_workflow_columns(cls, batch_size: int = 1000):
        """
        Uses the `workflow_columns` property to fill columns with data.
        """
        for column_name in cls.workflow_columns.keys():
            cls.populate_workflow_column(column_name, batch_size=batch_size)
