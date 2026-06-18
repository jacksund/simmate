# -*- coding: utf-8 -*-

import functools

import polars


def update_column(column_name: str):
    """
    Decorator for Datastore class methods.
    Iterates through all rows (chunk by chunk) and applies the decorated method
    to add or update a column.

    The decorated method should accept `(cls, df: polars.DataFrame, **kwargs)`
    and return a Polars Series or list containing the new column values.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(cls, parallel_job: bool = False, *args, **kwargs):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                new_values = func(cls, df, *args, **kwargs)
                return df.with_columns(
                    polars.Series(name=column_name, values=new_values)
                )

            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator


def update_table():
    """
    Decorator for Datastore class methods.
    Iterates through all rows (chunk by chunk) and applies the decorated method
    to modify the table.

    The decorated method should accept `(cls, df: polars.DataFrame, **kwargs)`
    and return the updated Polars DataFrame.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(cls, parallel_job: bool = False, *args, **kwargs):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                return func(cls, df, *args, **kwargs)

            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator
