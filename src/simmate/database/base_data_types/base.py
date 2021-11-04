# -*- coding: utf-8 -*-


# This is a work in progress, but I envision this can be a base class that
# all database models can inherit from. I also switch away from django naming
# conventions to ones more friendly to beginners

from django.db import models
from django_pandas.io import read_frame


class SearchResults(models.QuerySet):
    """
    This class adds some extra methods to the results returned from a database
    search. For example, if you searched all Structures and wanted to convert
    these to a pandas dataframe or even a list of pymatgen structures, you can
    now do...
        search_results = Structures.objects.all()
        dataframe = search_results.to_dataframe()
        structures = search_results.to_pymatgen
    """

    def to_dataframe(
        self,
        fieldnames=(),
        verbose=True,
        index=None,
        coerce_float=False,
        datetime_index=False,
    ):
        # This method is coppied from...
        # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py

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

    def to_pymatgen(self):

        # This method will only be for structures and other classes that
        # support this method. So we make sure the model has supports it first.
        if not hasattr(self.model, "to_pymatgen"):
            raise Exception(
                "This database model does not have a to_pymatgen method implemented"
            )

        # now we can iterate through the queryset and return the converted
        # pymatgen objects as a list
        return [obj.to_pymatgen() for obj in self]


# Copied this line from...
# # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py
DatabaseTableManager = models.Manager.from_queryset(SearchResults)


class DatabaseTable(models.Model):

    # I override the default manager with the one we define above, which has
    # extra methods useful for our querysets.
    objects = DatabaseTableManager()

    @classmethod
    def create_subclass(cls, name, **new_columns):
        """
        This method is useful for dynamically creating a subclass DatabaseTable
        from some abstract class.

        Let's take an example where we inherit from a Structure table. The two
        ways we create a NewTable below are exactly the same:

        NewTable(Structure):
            new_field1 = table_column.FloatField()
            new_field2 = table_column.FloatField()

        NewTable = Structure.create_subclass(
            name="NewTable",
            new_field1 = table_column.FloatField()
            new_field2 = table_column.FloatField()
        )

        While this might seem silly, it helps us avoid a bunch of boilerplate
        code when we need to redefine a bunch of relationships in every single
        child class (and always in the same way). A great example of it's utility
        is in local_calculations.relaxations.
        """

        # because we update values below, we make sure we are editting a copy of the dictionary
        new_columns = new_columns.copy()

        # BUG: I'm honestly not sure what this does, but it works...
        # https://stackoverflow.com/questions/27112816/dynamically-creating-django-models-with-type
        new_columns.update({"__module__": __name__, "Meta": {}})

        # Now we dynamically create a new class that inherits from this main
        # one and also adds the new columns to it.
        NewClass = type(name, (cls,), new_columns)

        return NewClass

    class Meta:
        abstract = True


# This line does NOTHING but rename a module. I have this because I want to use
# "table_column.CharField(...)" instead of models.CharField(...) in my Models.
# This let's beginners read my higher level classes and instantly understand what
# each thing represents -- without them needing to understand
# that Django Model == Database Table. Experts may find this annoying, so I'm
# sorry :(
from django.db import models as table_column
