# -*- coding: utf-8 -*-

import operator
from functools import reduce

import pandas


def filter_pandas_df(data: pandas.DataFrame, **kwargs) -> pandas.DataFrame:
    """
    Filters a pandas DataFrame using django-like ORM queries
    """

    checks = []
    for filter_key, filter_value in kwargs.items():

        column_name, metric = (
            filter_key.rsplit("__", 1) if "__" in filter_key else (filter_key, "exact")
        )
        column = data[column_name]

        if metric == "exact":
            check = column == filter_value
        elif metric == "gt":
            check = column > filter_value
        elif metric == "gte":
            check = column >= filter_value
        elif metric == "lt":
            check = column < filter_value
        elif metric == "lte":
            check = column <= filter_value
        elif metric == "range":
            check = column.between(*filter_value)
        elif metric == "in":
            check = column.isin(filter_value)
        elif metric == "contains":
            check = column.str.contains(filter_value)
        elif metric == "icontains":
            check = column.str.contains(filter_value, case=False)
        elif metric == "isnull":
            check = column.isna() if filter_value else column.notna()
        else:
            # as a last resort, we just try "exact" instead of raising an error
            # raise Exception(f"Unknown filter metric: {metric}")
            check = column == filter_value

        checks.append(check)

    return data[reduce(lambda x, y: x & y, checks)]


def filter_polars_df(data, **kwargs):  # polars.DataFrame -> polars.DataFrame
    """
    Filters a Polars DataFrame using django-like ORM queries
    """
    import polars  # not yet an official dep

    checks = []
    for filter_key, filter_value in kwargs.items():
        column_name, metric = (
            filter_key.rsplit("__", 1) if "__" in filter_key else (filter_key, "exact")
        )
        column = polars.col(column_name)

        if metric == "exact":
            check = column == filter_value
        elif metric == "gt":
            check = column > filter_value
        elif metric == "gte":
            check = column >= filter_value
        elif metric == "lt":
            check = column < filter_value
        elif metric == "lte":
            check = column <= filter_value
        elif metric == "range":
            low, high = filter_value
            check = column.is_between(low, high, closed="both")
        elif metric == "in":
            check = column.is_in(filter_value)
        elif metric == "contains":
            # Regex by default (similar to pandas .str.contains without case=False)
            check = column.str.contains(filter_value)
        elif metric == "icontains":
            # Case-insensitive via inline regex flag
            check = column.str.contains(f"(?i){filter_value}")
        elif metric == "isnull":
            check = column.is_null() if filter_value else column.is_not_null()
        else:
            # Fallback to exact match
            check = column == filter_value

        checks.append(check)

    combined = reduce(operator.and_, checks)
    return data.filter(combined)
