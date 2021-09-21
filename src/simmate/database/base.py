# -*- coding: utf-8 -*-


# This is a work in progress, but I envision this can be a base class that
# all database models can inherit from. I also switch away from django naming
# conventions to ones more friendly to beginners

from django.db import models
from django_pandas.io import read_frame


class SearchResults(models.QuerySet):
    """
    This class adds some extra methods to the results returned from a database
    search. For example, if you searched all Spacegroup and wanted to convert
    these to a pandas dataframe, you can now do...
        search_results = Spacegroup.objects.all()
        dataframe = search_results.to_dataframe()
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


# This line does NOTHING but rename a module. I have this because I want to use
# "table_column.CharField(...)" instead of models.CharField(...) in my Models. 
# This let's beginner read my higher level classes and instantly understand what
# each thing represents -- without them needing to understand
# that Django Model == Database Table. Experts may find this annoying, so I'm
# sorry :(
from django.db import models as table_column
