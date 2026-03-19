# -*- coding: utf-8 -*-

import inspect
import textwrap
import urllib
from functools import cache
from pathlib import Path

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

from simmate.config import settings
from simmate.database.utilities import check_db_conn
from simmate.utilities import get_attributes_doc

from .archive import ArchiveMixin
from .html_mixin import HTMLMixin
from .search_results import DatabaseTableManager, SearchResults

# The "as table_column" line does NOTHING but rename a module.
# I have this because I want to use "table_column.CharField(...)" instead
# of "models.CharField(...)" in my Models. This let's beginners read my
# higher level classes and instantly understand what each thing represents
# -- without them needing to understand that Django Model == Database Table.
# Experts may find this annoying, so I'm sorry :(


class DatabaseTable(models.Model, HTMLMixin, ArchiveMixin):
    """
    The base class for defining a table in the Simmate database. All tables and
    mixins inherit from this class.

    Usage is identical to
    [models in Django](https://docs.djangoproject.com/en/4.0/#the-model-layer)
    where this class only adds extra methods for convenience.
    """

    class Meta:
        abstract = True

    # -------------------------------------------------------------------------

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

    exclude_from_summary: list[str] = []
    """
    When writing output summaries, these columns will be ignored. This is useful
    if you have a column for storing raw data that isn't friendly to read in
    the yaml format. 'structure' is an example of a field we'd want to
    exclude because its not very readable and is available elsewhere.
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
        occurrence of of this issue, we use "table_name" instead.
        """
        return cls.__name__

    @classmethod
    @property
    def columns(cls):
        return cls._meta.get_fields()

    @classmethod
    def get_column_names(
        cls,
        include_parents: bool = True,
        include_to_one_relations: bool = True,
        include_to_many_relations: bool = False,
        include_one_to_one_reverse: bool = False,
        include_many_to_many_reverse: bool = False,
        include_one_to_many_reverse: bool = False,
        id_mode: bool = False,  # e.g. give "project_id" instead of "project"
    ) -> list[str]:
        """
        Returns a list of all the column names for this table. Kwargs are used to
        specify how to handle relation columns (ForeignKey, ManyToManyField,
        OneToOneField, and their reverses). There is also an option to toggle
        whether inherited columns should be included.
        """
        column_names = []
        for column in cls._meta.get_fields(include_parents):

            name = column.name

            # there is some redundant code here, but organizing in this way
            # makes the logic a lot easier to follow

            if column.many_to_one:  # i.e. a Foreign Key
                if not include_to_one_relations:
                    continue
                if id_mode:
                    name += "_id"

            elif column.one_to_many:  # i.e. reverse of Foreign Key
                if not include_to_many_relations or not include_one_to_many_reverse:
                    continue
                if id_mode:
                    name += "__ids"

            elif column.one_to_one:  # OneToOne that can be on either model
                if not include_to_one_relations:
                    continue
                is_reverse = not hasattr(cls, f"{column.name}_id")
                if is_reverse and not include_one_to_one_reverse:
                    continue
                if id_mode:
                    if is_reverse:
                        name += "__id"
                    else:
                        name += "_id"  # bc this is an actual col in the db

            elif column.many_to_many:  # ManyToMany that can be on either model
                if not include_to_many_relations:
                    continue
                is_reverse = getattr(cls, column.name).reverse
                if is_reverse and not include_many_to_many_reverse:
                    continue
                if id_mode:
                    name += "__ids"

            column_names.append(name)

        return column_names

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
        return {
            "name": cls.html_display_name if cls.html_display_name else cls.table_name,
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

        These are typically all from the `simmate.database.mixins`
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
        from simmate.database.mixins import (
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
            from simmate.workflows.utilities import get_workflow

            from .calculation import Calculation

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
    # Methods that set up the REST API and filters that can be queried with
    # -------------------------------------------------------------------------

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

            # to prevent crazy joins, we can limit the number of double-underscores
            # (which indicate a join or field lookup) in a filter.
            # Example: `user__first_name__isnull` has 2 double-underscores.
            # `a__b__c__d` is allowed, but `a__b__c__d__e` is not.
            max_joins = settings.website.max_filter_joins
            if max_joins is not None and filter_name.count("__") > max_joins:
                raise Exception(
                    f"The filter '{filter_name}' contains too many double-underscores. "
                    f"A maximum of {max_joins} is allowed to prevent excessively "
                    "complex database joins."
                )

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

            # ex: a `tags` m2m column and the filter is `tags__ids=[1,2,3,...]`.
            elif filter_name.endswith("__ids") and hasattr(cls, f"{filter_name[:-5]}"):
                relation = f"{filter_name[:-5]}__id"  # eg `tags__id`
                # Note: filter_methods like `filter_tag_ids` would take priority
                # and should be used when possible
                if filter_value == []:
                    queryset = queryset.filter(**{relation: []})
                else:
                    # By default we filter down to entries that have all of the
                    # listed ids linked. So a tags__ids=[1,3] query would match
                    # entries where tag_ids=[1,2,3,4,5] but NOT tag_ids=[2,3,4,5].
                    # For alternative ways to filter (e.g. using `tags__in` or
                    # a full list match) a custom filter method should be defined
                    for i in filter_value:
                        queryset = queryset.filter(**{relation: i})

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

    # -------------------------------------------------------------------------

    @classmethod
    def get_curated_df(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects
        return queryset.to_dataframe()  # default to just raw data
