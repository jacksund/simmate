# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

# !!! This mixin is at the outlining & planning stage. Do not use in prod yet.


class FilteredScope(DatabaseTable):
    """
    Captures a set of filtering critera to be applied to some model/table.

    This is useful for projects where you'd define scopes that need to be
    repeatedly ran on large datasets. For example, a chemistry project might
    be "scoped" to molecules with X substructure and YZ property limits. This
    scope can capture that info and later be applied to larger datasets like
    Enamine, Emolecules, etc.
    """

    class Meta:
        abstract = True

    scope_label = table_column.TextField(blank=True, null=True)
    """
    Label to classify the resulting matches in the scope. You can think of this
    as a "tag" that will be applied to all matching entries.
    """

    scope_config = table_column.JSONField(blank=True, null=True)
    """
    The filter stored as a JSON list. Each item in the list is 1 django filter
    condition.
    
    For example, this django query:
    
    ``` python
    SomeTable.objects.filter(
        column_A__gte=123,
        column_B__range=(123,321),
        column_C__isnull=False,
    )
    ```
    
    Would have the following config:
    
    ``` python
    {
     "column_A__gte": 123,
     "column_B__range": (123,321)
     "column_C__isnull": False,
    }
    ```
    
    Advanced django syntax (like Q clauses) are not yet supported
    """

    scoped_model = table_column.TextField(blank=True, null=True)
    """
    Model name that this scope's config should be applied to. For some subclasses,
    this is a constant / assumed.
    """

    # -------------------------------------------------------------------------

    # While a python programmer can write out the scope_config on their own,
    # a web UI needs more guidance. These configs below help populate forms in
    # a human-readbale way & also make sure the available filters make sense
    # for the column selected.

    # see https://docs.djangoproject.com/en/5.0/ref/models/querysets/#field-lookups
    field_lookups_config = {
        "exact": "is exactly (aka equals)",
        "iexact": "is exactly (case insensitive)",
        "contains": "contains the text",
        "icontains": "contains the text (case insensitive)",
        "in": "is within the list",
        "gt": "is greater than",
        "gte": "is greater than or equal to",
        "lt": "is less than",
        "lte": "is less than or equal to",
        "startswith": "starts with the text",
        "istartswith": "starts with the text (case insensitive)",
        "endswith": "ends with the text",
        "iendswith": "ends with the text (case insensitive)",
        "range": "is within the range",
        # year/month/day/etc need a 2nd modifier like exact or gte
        "date": "has the datetime",
        "year": "where the year is",
        "month": "where the month is",
        "day": "where the day is",
        "week": "where the week is",
        "week_day": "where the week_day is",
        "quarter": "where the quarter is",
        "time": "where the time is",
        "hour": "where the hour is",
        "minute": "where the minute is",
        "second": "where the second is",
        # iso_year + iso_week_day !!! -> not sure how this differs from year. I think its for
        # cross-timezone comparisons
        "isnull": "is empty (null)",
        "regex": "matches the following regular expression",
        "iregex": "matches the following regular expression (case insensitive)",
    }
    lookup_type_defaults = {
        # TODO: change keys to classes (e.g. table_column.FloatField)
        "FloatField": [
            # !!! warning, no rounding done
            "exact",
            "in",
            "gt",
            "gte",
            "lt",
            "lte",
            "range",
            "isnull",
        ],
        "IntegerField": [
            "exact",
            "in",
            "gt",
            "gte",
            "lt",
            "lte",
            "range",
            "isnull",
        ],
        "TextField": [
            "exact",
            "iexact",
            "contains",
            "icontains",
            "startswith",
            "istartswith",
            "endswith",
            "iendswitch",
            "regex",
            "iregex",
            "isnull",
        ],
    }
