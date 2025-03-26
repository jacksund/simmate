# -*- coding: utf-8 -*-

from functools import reduce

import pandas


def filter_df(data: pandas.DataFrame, **kwargs) -> pandas.DataFrame:
    """
    Filters a pandas DataFrame using django-like ORM queries.

    The endgoal of this util is to make code cleaner and filters easier to read.
    This comes at a cost of being slightly slower.
    """
    filter_condition_checks = []
    for filter_key, filter_value in kwargs.items():
        column, metric = (
            filter_key.rsplit("__", 1) if "__" in filter_key else (filter_key, "exact")
        )
        if metric == "exact":
            check = data[column] == filter_value
        elif metric == "gte":
            check = data[column] >= filter_value
        elif metric == "lte":
            check = data[column] <= filter_value
        elif metric == "range":
            check = data[column].between(*filter_value)
        elif metric == "in":
            check = data[column].isin(filter_value)
        elif metric == "contains":
            check = data[column].str.contains(filter_value)
        elif metric == "icontains":
            check = data[column].str.contains(filter_value, case=False)
        else:
            # as a last resort, we just try "exact" instead of raising an error
            # raise Exception(f"Unknown filter metric: {metric}")
            check = data[column] == filter_value
        filter_condition_checks.append(check)
    return data[reduce(lambda x, y: x & y, filter_condition_checks)]
