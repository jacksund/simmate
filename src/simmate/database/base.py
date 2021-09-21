# -*- coding: utf-8 -*-


# This is a work in progress, but I envision this can be a base class that
# all database models can inherit from. I also switch away from django naming
# conventions to ones more friendly to beginners

from django.db import models
from django_pandas.io import read_frame


class SearchResults(models.QuerySet):
    def to_dataframe(
        self,
        fieldnames=(),
        verbose=True,
        index=None,
        coerce_float=False,
        datetime_index=False,
    ):
        """
        Returns a DataFrame from the queryset
        Paramaters
        -----------
        fieldnames:  The model field names(columns) to utilise in creating
                     the DataFrame. You can span a relationships in the usual
                     Django ORM way by using the foreign key field name
                     separated by double underscores and refer to a field
                     in a related model.
        index:  specify the field to use  for the index. If the index
                field is not in fieldnames it will be appended. This
                is mandatory for timeseries.
        verbose: If  this is ``True`` then populate the DataFrame with the
                 human readable versions for foreign key fields else
                 use the actual values set in the model
        coerce_float:   Attempt to convert values to non-string, non-numeric
                        objects (like decimal.Decimal) to floating point.
        datetime_index: specify whether index should be converted to a
                        DateTimeIndex.
        """
        # This method is coppied from...
        # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py
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
        # support this method.
        # Another thing to note is that Manager methods can access self.model
        # to get the model class to which they’re attached.
        return "TESTING-123"


# Copied this line from...
# # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py
DatabaseTableManager = models.Manager.from_queryset(SearchResults)


class DatabaseTable(models.Model):

    # I override the default manager with the one we define above, which has
    # extra methods useful for our querysets.
    objects = DatabaseTableManager()

    class Meta:
        abstract = True


# This line does NOTHING but rename a module. I have this because I want to do...
#   table_column.CharField(...)
# instead of ...
#   models.CharField(...)
# in my Models. This let's beginner read my higher level classes and instantly
# understand what each thing represents -- without them needing to understand
# that Django Model == Database Table. Experts may find this annoying, so I'm
# sorry :(
from django.db import models as table_column
