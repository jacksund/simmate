# -*- coding: utf-8 -*-

"""
This module defines the lowest-level classes for database tables and their
search results.
"""


import os
import inspect
import shutil

import yaml

import pandas
from django.db import models, transaction
from django_pandas.io import read_frame

from typing import List


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
    ):
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

    def to_toolkit(self):
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

    def to_archive(self, filename_base: str = None):
        """
        Writes a compressed zip file using the table's base_info attribute.
        Underneath, the file is written in a csv format.

        This is useful for small making archive files and reloading fixtures
        to a separate database.

        This method is attached to the table manager for scenarios to allow
        queryset filtering before dumping data.

        To load this database dump into a new database, use the class's
        `from_mini_dump` method.

        Parameters
        -----------

        - `filename_base`:
            The filename to write the zip file to. By defualt, None will make
            a filename named MyExampleTableName.zip. Do not include the file extension
            (.zip) in this parameter.

        """

        # generate the file name if one wasn't given
        if not filename_base:
            filename_base = self.model.__name__

        # We want to load the entire table, but only grab the fields that
        # are in base_info.
        base_objs = self.only(*self.model.base_info)

        # now convert these objects to a pandas dataframe, again using just
        # the base_info columns
        df = base_objs.to_dataframe(fieldnames=self.model.base_info)

        # Write the data to a csv file
        # OPTIMIZE: is there a better format that pandas can write to?
        csv_filename = filename_base + ".csv"
        df.to_csv(csv_filename, index=False)

        # now convert the dump file to a compressed zip
        shutil.make_archive(
            filename_base,
            "zip",
            ".",  # says file is in the current working directory
            csv_filename,
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
DatabaseTableManager = models.Manager.from_queryset(SearchResults)


class DatabaseTable(models.Model):
    """
    The base class for defining a table in the Simmate database. All tables and
    mixins inherit from this class.

    Usage is identical to
    [Models in Django](https://docs.djangoproject.com/en/4.0/#the-model-layer)
    where this class only adds extra methods for convenience.
    """

    class Meta:
        abstract = True

    # I override the default manager with the one we define above, which has
    # extra methods useful for our querysets.
    objects = DatabaseTableManager()
    """
    Accesses all of the rows in this datatable and initiates SearchResults
    """

    @classmethod
    def show_columns(cls):
        """
        Prints a list of all the column names for this table and indicates which
        columns are related to other tables. This is primarily used to help users
        interactively view what data is available.
        """
        # Iterate through and grab the columns
        column_names = [
            column.name + f" (relation to {column.related_model.__name__})"
            if column.is_relation
            else column.name
            for column in cls._meta.get_fields()
        ]

        # Then use yaml to make the printout pretty (no quotes and separate lines)
        print(yaml.dump(column_names))

    @classmethod
    def create_subclass(cls, name: str, module: str, **new_columns):
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
        new_columns.update(
            {
                "__module__": module,
                "Meta": {},
            }
        )
        # TODO: make it so I don't have to specify the module, but it is automatically
        # detected from where the class is created. This would remove boilerplate code.
        # A good start to this is here:
        #   https://stackoverflow.com/questions/59912684/
        # sys._getframe(1).f_globals["__name__"]  <-- grabs where this function is called
        # but doesn't work for multiple levels of inheritance. For example, this fails for
        # the Relaxation subclasses because the create_all_subclasses method calls
        # create_subclass -- therefore we'd need _getframe(3) instead of 1...

        # Now we dynamically create a new class that inherits from this main
        # one and also adds the new columns to it.
        NewClass = type(name, (cls,), new_columns)

        return NewClass

    @classmethod
    def from_toolkit(cls, as_dict=False, **kwargs):
        """
        Given fundamental "base_info" and toolkit objects, this method will populate
        all relevant columns.

        If the table is made up of multiple mix-ins, this method iterates through
        each of the `_from_toolkit` methods of those mixins and combines the results.
        Therefore, you must view this method for each mix-ins to determine which
        kwargs must be passed.

        Parameters
        ----------
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
        # TODO: How should I best handle passing extra kwargs to the final class
        # initialization? For example, I would want to pass `energy` but I wouldn't
        # want to pass the toolkit structure object. I may update this line in
        # the future to remove python objects. For now, I only remove structure
        # becauase I know that it is a toolkit object -- not a database column
        all_data = kwargs.copy()
        all_data.pop("structure", None)  # None ignores error if structure not present

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

    @classmethod
    @transaction.atomic
    def load_archive(cls, filename: str = None):
        """
        Reads a compressed zip file made by `objects.to_mini_dump` and loads the data
        back into the Simmate database.

        Typically, users won't call this method directly, but instead use the
        `load_remote_archive` method, which handles downloading the archive
        file from the Simmate website for you.

        Parameters
        -----------

        - `filename`:
            The filename to write the zip file to. By defualt, None will try to
            find a file named MyExampleTableName.zip.
        """

        from tqdm import tqdm
        from pymatgen.core.structure import Structure as Structure_PMG

        # generate the file name if one wasn't given
        if not filename:
            filename = cls.__name__ + ".zip"

        # uncompress the zip file
        shutil.unpack_archive(filename)

        # We will now have a csv file of the same name, which we load into
        # a pandas dataframe
        df = pandas.read_csv(filename.replace(".zip", ".csv"))

        # convert the dataframe to a list of dictionaries that we will iterate
        # through.
        entries = df.to_dict(orient="records")

        # For all entries, convert the structure_string to a toolkit structure
        # OPTIMIZE: is there a better way to do decide which entries need to be
        # converted to toolkit structures? This code may be better placed in
        # base_data_type methods (e.g. a from_base_info method for each)
        if "structure_string" in df.columns:

            for entry in tqdm(entries):
                structure_str = entry.pop("structure_string")
                # !!! This code is a copy of base_data_types.Structure.to_toolkit
                # This should instead be a method attached to ToolkitStructure
                storage_format = "CIF" if (structure_str[0] == "#") else "POSCAR"
                structure = Structure_PMG.from_str(
                    structure_str,
                    fmt=storage_format,
                )
                # !!!
                entry["structure"] = structure

        # now iterate through all entries to save them to the database
        for entry in tqdm(entries):
            entry_db = cls.from_toolkit(**entry)
            entry_db.save()


# This line does NOTHING but rename a module. I have this because I want to use
# "table_column.CharField(...)" instead of models.CharField(...) in my Models.
# This let's beginners read my higher level classes and instantly understand what
# each thing represents -- without them needing to understand
# that Django Model == Database Table. Experts may find this annoying, so I'm
# sorry :(
from django.db import models as table_column
