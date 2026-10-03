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

    Pass `df=...` to apply the method to an in-memory DataFrame instead of
    the chunk files. The updated DataFrame is returned.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(
            cls,
            *args,
            df: polars.DataFrame | None = None,
            parallel_job: bool = False,
            **kwargs,
        ):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                new_values = func(cls, df, *args, **kwargs)
                return df.with_columns(
                    polars.Series(name=column_name, values=new_values)
                )

            if df is not None:
                return transform(df)
            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator


def update_table(skip_nulls: str | None = None):
    """
    Decorator for Datastore class methods.
    Iterates through all rows (chunk by chunk) and applies the decorated method
    to modify the table.

    The decorated method should accept `(cls, df: polars.DataFrame, **kwargs)`
    and return the updated Polars DataFrame.

    If `skip_nulls` is given a column name, the method is only applied to rows
    where that column is not null. All other rows are kept as-is (with nulls
    for any new columns) and row order is preserved.

    Pass `df=...` to apply the method to an in-memory DataFrame instead of
    the chunk files. The updated DataFrame is returned.
    """

    def decorator(func):
        if skip_nulls:
            func = _skip_null_rows(func, skip_nulls)

        @functools.wraps(func)
        def wrapper(
            cls,
            *args,
            df: polars.DataFrame | None = None,
            parallel_job: bool = False,
            **kwargs,
        ):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                return func(cls, df, *args, **kwargs)

            if df is not None:
                return transform(df)
            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator


def _skip_null_rows(func, column: str):
    """
    Wraps a `(cls, df, **kwargs) -> df` method so that it is only applied to
    rows where `column` is not null.
    """

    @functools.wraps(func)
    def wrapper(cls, df: polars.DataFrame, *args, **kwargs) -> polars.DataFrame:
        is_null = df[column].is_null()
        if not is_null.any():
            return func(cls, df, *args, **kwargs)

        # the method is still called when all rows are null (with an empty
        # df) so that new columns + dtypes are consistent across chunks
        df = df.with_row_index("_row_idx")
        df_updated = func(cls, df.filter(~is_null), *args, **kwargs)
        return (
            polars.concat([df_updated, df.filter(is_null)], how="diagonal_relaxed")
            .sort("_row_idx")
            .drop("_row_idx")
        )

    return wrapper
