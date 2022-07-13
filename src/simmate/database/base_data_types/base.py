# -*- coding: utf-8 -*-

"""
This module defines the lowest-level classes for database tables and their
search results.

See the `simmate.database.base_data_types` (which is the parent module of 
this one) for example usage.
"""

import os
import inspect
import shutil
import urllib
import warnings

import yaml

import pandas
from django.db import models  # , transaction
from django_pandas.io import read_frame
from django.utils.timezone import datetime

from typing import List

# This line does NOTHING but rename a module. I have this because I want to use
# "table_column.CharField(...)" instead of "models.CharField(...)" in my Models.
# This let's beginners read my higher level classes and instantly understand what
# each thing represents -- without them needing to understand
# that Django Model == Database Table. Experts may find this annoying, so I'm
# sorry :(
from django.db import models as table_column


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
        fieldnames: List[str] = (),
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

    def to_archive(self, filename: str = None):
        """
        Writes a compressed zip file using the table's base_info attribute.
        Underneath, the file is written in a csv format.

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
                    self.model.__name__,
                    str(today.year),
                    str(today.month).zfill(2),
                    str(today.day).zfill(2),
                ]
            )
            filename = filename_base + ".zip"

        # Turn the filename into the full path. We do this because we only
        # want to
        # filename = os.path.abspath(filename)
        # os.path.dirname(filename)

        # grab the base_information, and if ID is not present, add it
        base_info = self.model.base_info
        if "id" not in base_info:
            base_info.append("id")
        # if "created_at" not in base_info:
        #     base_info.append("created_at")
        # if "updated_at" not in base_info:
        #     base_info.append("updated_at")

        # We want to load the entire table, but only grab the fields that
        # are in base_info.
        base_objs = self.only(*base_info)

        # now convert these objects to a pandas dataframe, again using just
        # the base_info columns
        df = base_objs.to_dataframe(fieldnames=base_info)

        # Write the data to a csv file
        # OPTIMIZE: is there a better format that pandas can write to?
        csv_filename = filename.replace(".zip", ".csv")
        df.to_csv(csv_filename, index=False)

        # now convert the dump file to a compressed zip. In the complex, os
        # functions below we are just grabbing the filename without the
        # zip ending. We are also grabbing the directory that the csv is
        # located in
        shutil.make_archive(
            base_name=filename.removesuffix(".zip"),
            format="zip",
            root_dir=os.path.dirname(os.path.abspath(csv_filename)),
            base_dir=os.path.basename(csv_filename),
        )

        # we can now delete the csv file
        os.remove(csv_filename)

    # EXPERIMENTAL
    # from prefect import Client
    # from prefect.utilities.graphql import with_args
    # def get_prefect_fields(self, fields):
    #     # This is only every used for Calculations! I have it here instead of making
    #     # whole new Manager subclass for simplicity.
    #     # Make sure we have a calculation by seeing if it has prefect_flow_run_id
    #     # field attached to the model
    #     if not hasattr(self.model, "prefect_flow_run_id"):
    #         raise Exception("get_prefect_fields() should only be used on Calculations!")
    #     # grab all the ids in the queryset
    #     ids = list(self.values_list("prefect_flow_run_id", flat=True).all())
    #     # now for all of the ids in this queryset, grab the corresponding info
    #     query = {
    #         "query": {
    #             with_args(
    #                 "flow_run",
    #                 {
    #                     "where": {
    #                         "id": {"_in": ids},
    #                     },
    #                 },
    #             ): fields,
    #         }
    #     }
    #     client = Client()
    #     result = client.graphql(query)
    #     return result


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

    base_info: List[str] = []
    """
    The base information for this database table and only these fields are stored
    when the `to_archive` method is used. Using the columns in this list, all 
    other columns for this table can be calculated, so the columns in this list 
    are effectively the "raw data".
    """
    # TODO: setting base_info is becoming boilerplate. Consider making this
    # into a method like to_toolkit that automatically looks at all mix-ins
    # and creates this list (i.e. involves _base_info properties)

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

    @classmethod
    def get_table_name(cls) -> str:
        """
        Returns the name of this database table, which will simply match the
        class name. Using `Table.__name__` is often easier. This method simply
        makes the name accessible in Django Templates.
        """
        return cls.__name__

    @classmethod
    def create_subclass(
        cls,
        name: str,
        module: str,
        app_label: str = None,
        **new_columns,
    ):
        """
        This method is useful for dynamically creating a subclass DatabaseTable
        from some abstract class.

        Let's take an example where we inherit from a Structure table. The two
        ways we create a NewTable below are exactly the same:

        ``` python
        # Normal way to create a child class
        NewTable(Structure):
            new_field1 = table_column.FloatField()
            new_field2 = table_column.FloatField()

        # How this method makes the same child class
        NewTable = Structure.create_subclass(
            name="NewTable",
            module=__name__, # required for serialization
            new_field1 = table_column.FloatField()
            new_field2 = table_column.FloatField()
            # app_label --> typically not required bc the parent class sets this
        )
        ```

        While this might seem silly, it helps us avoid a bunch of boilerplate
        code when we need to redefine a bunch of relationships in every single
        child class (and always in the same way). A great example of it's utility
        is in `simmate.calculators.vasp.database.relaxation`.
        """

        # because we update values below, we make sure we are editting a
        # copy of the dictionary
        new_columns = new_columns.copy()

        # BUG: I'm honestly not sure what this does, but it works...
        # https://stackoverflow.com/questions/27112816/
        # For a more robust way of setting the Meta class, see my code in
        # simmate.website.workflows.utilities
        new_columns.update(
            {
                "__module__": module,
                "Meta": {"app_label": app_label} if app_label else {},
            }
        )
        # TODO: make it so I don't have to specify the module, but it is automatically
        # detected from where the class is created. This would remove boilerplate code.
        # A good start to this is here:
        #   https://stackoverflow.com/questions/59912684/
        # sys._getframe(1).f_globals["__name__"]  <-- grabs where this function is called
        # but doesn't work for multiple levels of inheritance. For example, this fails for
        # the Relaxation subclasses because the create_subclasses method calls
        # create_subclass -- therefore we'd need _getframe(3) instead of 1...

        # Now we dynamically create a new class that inherits from this main
        # one and also adds the new columns to it.
        NewClass = type(name, (cls,), new_columns)

        return NewClass

    @classmethod
    def from_toolkit(cls, as_dict: bool = False, **kwargs):
        """
        Given fundamental "base_info" and toolkit objects, this method will populate
        all relevant columns.

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

    def update_from_toolkit(self, **kwargs):
        """
        Given fundamental "base_info" and toolkit objects, this method will populate
        all relevant columns.

        This method is meant for updating existing database entries with new
        data. If your creating a brand-new database entry, use the
        `from_toolkit` method instead.
        """
        new_kwargs = self.from_toolkit(as_dict=True, **kwargs)
        for new_kwarg, new_value in new_kwargs.items():
            setattr(self, new_kwarg, new_value)
        self.save()

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

    # @transaction.atomic  # We can't have an atomic transaction if we use Dask
    @classmethod
    def load_archive(
        cls,
        filename: str = None,
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

        from tqdm import tqdm
        from simmate.toolkit import Structure as ToolkitStructure

        # generate the file name if one wasn't given
        if not filename:
            # The name will be something like "MyExampleTable-2022-01-25.zip".
            # We go through all files that match "MyExampleTable-*.zip" and then
            # grab the most recent date.
            matching_files = [
                file
                for file in os.listdir()
                if file.startswith(cls.__name__) and file.endswith(".zip")
            ]
            # make sure there is at least one file
            if not matching_files:
                raise FileNotFoundError(
                    f"No file found matching the {cls.__name__}-*.zip format"
                )
            # sort the files by date and grab the first
            matching_files.sort(reverse=True)
            filename = matching_files[0]

        # Turn the filename into the full path -- which makes a number of
        # manipulations easier below.
        filename = os.path.abspath(filename)

        # uncompress the zip file to the same directory that it is located in
        shutil.unpack_archive(
            filename,
            extract_dir=os.path.dirname(filename),
        )

        # We will now have a csv file of the same name, which we load into
        # a pandas dataframe
        csv_filename = filename.replace(".zip", ".csv")
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

            # For all entries, convert the structure_string to a toolkit structure
            if "structure_string" in entry:
                structure_str = entry.pop("structure_string")
                structure = ToolkitStructure.from_database_string(structure_str)
                entry["structure"] = structure
            # OPTIMIZE: is there a better way to do decide which entries need to be
            # converted to toolkit objects? This code may be better placed in
            # base_data_type methods (e.g. a `from_base_info` method for each)

            entry_db = cls.from_toolkit(**entry)
            entry_db.save()

        # now iterate through all entries to save them to the database
        if not parallel:
            # If user doesn't want parallelization, we run these in the main
            # thread and monitor progress with tqdm
            for entry in tqdm(entries):
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
        os.remove(csv_filename)
        if delete_on_completion:
            os.remove(filename)  # the zip archive

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
            print(
                "\nWARNING: this data is NOT from the Simmate team, so be sure "
                "to visit the provider's website and to cite their work."
                f" This data is from {cls.source} and the following paper "
                f"should be cited: {cls.source_doi}\n"
            )

        # Predetermine the file name, which is just the ending of the URL
        archive_filename = remote_archive_link.split("/")[-1]

        # Download the archive zip file from the URL to the current working dir
        print("Downloading archive file...")
        urllib.request.urlretrieve(remote_archive_link, archive_filename)
        print("Done.\n")

        # now that the archive is downloaded, we can load it into our db
        print("Loading data into Simmate database...")
        cls.load_archive(
            archive_filename,
            delete_on_completion=True,
            confirm_override=True,  # we already confirmed this above
            parallel=parallel,
            confirm_sqlite_parallel=True,  # we already confirmed this above
        )
        print("Done.\n")

    @classmethod
    def get_column_names(cls) -> List[str]:
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
            column.name + f" (relation to {column.related_model.__name__})"
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
            if hasattr(simmate_mixins, parent.__name__)
            and parent.__name__ != "DatabaseTable"
        ]

    @classmethod
    def get_mixin_names(cls) -> List[str]:
        """
        Grabs the mix-in Tables that were used to make this class and returns
        a list of their names.
        """
        return [mixin.__name__ for mixin in cls.get_mixins()]

    @classmethod
    def get_extra_columns(cls) -> List[str]:
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
