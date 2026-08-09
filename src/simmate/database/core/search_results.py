# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

import pandas
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import datetime, now, timedelta

from simmate.config import settings
from simmate.database.utils import check_db_conn


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
        columns: list[str] = (),
        exclude_columns: list[str] = (),
        limit: int = None,
        use_cache: bool = True,
        engine: str = "pandas",
    ):
        """
        Returns a Pandas DataFrame of the search results

        Paramaters
        -----------
        - `columns`:
            The model field names (columns) to utilise in creating the DataFrame.
            You can span a relationships in the usual Django ORM way by using
            the foreign key field name separated by double underscores and refer
            to a field in a related model.
        - `exclude_columns`:
            If columns is left as None (meaning use all cols), this is the
            list of cols that will be ignored from the full default list.
        - `limit`:
            whether to limit the total number of rows. This is the equivalent
            of `.all()[:limit].to_dataframe()`
        - `use_cache`:
            whether to use django's result cache if the query has been executed
            already
        - `engine`:
            The DataFrame engine to use. Options are "pandas" (default) or
            "polars". When "polars", a polars.DataFrame is returned instead
            of a pandas.DataFrame.
        """

        # This method originally used `django_pandas` but we since decided to
        # implement our own method that is optimized for our own use cases and avoids
        # cases where the queryset is accidentally ran twice:
        # https://github.com/chrisdev/django-pandas/blob/master/django_pandas/
        # https://github.com/chrisdev/django-pandas/issues/138

        if not columns:
            has_user_cols = False
            columns = [
                c
                for c in self.model.get_column_names(id_mode=True)
                if c not in exclude_columns
            ]
        else:
            has_user_cols = True

        values_list = None  # set dynamically

        # check if the query has been executed already. If so, we use those cached
        # results to get our values_list. (unless the query gave back an
        # incomplete values_list)
        if use_cache and self._result_cache is not None:

            # check if we have a list of models or values
            if self._iterable_class == models.query.ValuesListIterable:

                # if the user has a `values_list` call to the queryset, and didn't
                # set columns for `to_dataframe`, we'll use those cols for the df
                if not has_user_cols:
                    columns = list(self._fields)
                    values_list = list(self)

                # otherwise, we need to make sure that we have all the values
                # needed for the dataframe If not, another query is needed
                else:
                    cache_columns = list(self._fields)
                    has_all_cols = all([c in cache_columns for c in columns])
                    if has_all_cols:
                        i_map = [cache_columns.index(c) for c in columns]
                        values_list = [
                            tuple([entry[i] for i in i_map]) for entry in self
                        ]
                    # else:
                    #     logging.warning(
                    #         "Cached values list is incompatible with the requested "
                    #         "dataframe columns list. A new db query will be ran "
                    #         "to fix this. "
                    #     )
                    #     # we leave values_list=None so we get new query below

            # otherwise we have a list of models. We'll have to trust that
            # the user properly used `select_related` and `only` ahead of time.
            # Optimization falls on them since the query was already executed
            else:
                # logging.warning(
                #     "You are using the query cache to generate a dataframe. "
                #     "Make sure you used `select_related` and `only` on your queryset "
                #     "to properly optimize your query. Otherwise this next call "
                #     "will be extremely slow: "
                # )
                values_list = [
                    tuple([getattr(entry, col) for col in columns]) for entry in self
                ]

            # limit if it was requested
            if values_list and limit:
                values_list = values_list[:limit]

        # if the query hasn't been ran yet, we can make sure we run an optimized
        # query -- one were we only grab the relevent columns and skip object
        # generation
        if not values_list:
            query = (
                self.values_list(*columns)
                if not limit
                else self.values_list(*columns)[:limit]
            )
            values_list = list(query)

        if engine == "pandas":
            df = pandas.DataFrame.from_records(
                data=values_list,
                columns=columns,
            )
        elif engine == "polars":
            import polars

            df = polars.DataFrame(
                data=values_list,
                schema=columns,
                orient="row",
                infer_schema_length=None,
            )
        else:
            raise ValueError(
                f"Unknown engine '{engine}'. Supported: 'pandas', 'polars'"
            )

        # TODO: change choice fields to verbose
        # TODO: add toolkit col

        return df

    def to_curated_dataframe(self) -> pandas.DataFrame:
        """
        Converts your SearchResults to a list of pymatgen objects
        """
        return self.model.get_curated_df(self)

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

    def to_archive(self, filename: Path | str = None):
        """
        Writes a compressed zip file using the table's `archive_fieldset`
        attribute. Underneath, the file is written in a csv format.

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
                    self.model.table_name,
                    str(today.year),
                    str(today.month).zfill(2),
                    str(today.day).zfill(2),
                ]
            )
            filename = filename_base + ".zip"

        # convert to path obj
        filename = Path(filename)

        # now convert these objects to a pandas dataframe, using just
        # the archive columns that are being stored
        df = self.to_dataframe(columns=self.model.archive_fieldset)

        # Write the data to a csv file
        # OPTIMIZE: is there a better format that pandas can write to?
        csv_filename = filename.with_suffix(".csv")
        df.to_csv(csv_filename, index=False)

        # now convert the dump file to a compressed zip. In the complex, os
        # functions below we are just grabbing the filename without the
        # zip ending. We are also grabbing the directory that the csv is
        # located in
        shutil.make_archive(
            base_name=filename.with_suffix(""),  # removes .zip ending
            format="zip",
            root_dir=csv_filename.absolute().parent,
            base_dir=csv_filename.name,
        )

        # we can now delete the csv file
        csv_filename.unlink()

    def to_api_dict(
        self, next_url: str = None, previous_url: str = None, **kwargs
    ) -> dict:
        """
        Converts the search results to a API dictionary. This is used to generate
        the default API response and can be overwritten.

        Note, this is typically called on the *page* object list, and not the
        full query results.
        """
        # We follow the list api format that django rest_framework uses. The
        # next/previous is for pagination
        return {
            # OPTIMIZE: counting can take ~20 sec for ~10 mil rows, which is
            # terrible for a web UI. I tried a series of fixes but no luck:
            #   https://stackoverflow.com/questions/55018986/
            "count": self.count(),
            "next": next_url,
            "previous": previous_url,
            "results": [entry.to_api_dict(**kwargs) for entry in self.all()],
        }

    def to_json_response(self, **kwargs) -> JsonResponse:
        """
        Takes the API dictionary (from `to_api_dict`) and converts it to a
        Django JSON reponse
        """
        return JsonResponse(self.to_api_dict(**kwargs))

    def to_csv_response(self, mode: str = "api", **kwargs) -> HttpResponse:
        if mode == "curated":
            df = self.model.get_curated_df(self)
        elif mode == "api":
            df = self.to_dataframe()
        else:
            raise Exception(f"Unknown `mode` for `to_csv_response`: {mode}")

        # https://stackoverflow.com/questions/54729411/
        response = HttpResponse(content_type="text/csv")
        date_str = now().strftime("%Y_%m_%d")  # e.g. 2025_10_31
        response["Content-Disposition"] = (
            f"attachment; filename={date_str}_simmate_{self.model.__name__}.csv"
        )
        df.to_csv(path_or_buf=response, index=False)
        return response

    # -------------------------------------------------------------------------

    def filter_by_tags(self, tags: list[str]):
        """
        A utility filter() method that helps query the 'tags' column of a table.

        NOTE: Pay close attention to filtering when using the SQLite3 backend
        as Django warns about unexpected substring matching:
            https://docs.djangoproject.com/en/4.2/ref/databases/#substring-matching-and-case-sensitivity
        """

        if tags:
            new_query = self
            for tag in tags:
                if settings.database_backend == "postgresql":
                    new_query = new_query.filter(tags__contains=tag)
                elif settings.database_backend == "sqlite3":
                    new_query = new_query.filter(tags__icontains=tag)
        else:
            new_query = self.filter(tags=[])

        return new_query

    # -------------------------------------------------------------------------

    # These methods behaves exactly the save as django's default ones, but they
    # are wrapped to catch errors such as "connection closed" failures
    # and retries with a new connection.

    @check_db_conn
    def bulk_create(self, *args, **kwargs):
        return super().bulk_create(*args, **kwargs)

    @check_db_conn
    def bulk_update(self, *args, **kwargs):
        return super().bulk_update(*args, **kwargs)

    # -------------------------------------------------------------------------

    # Misc utilities for common tasks

    def filter_age(self, cutoff: str, age_column: str = "created_at"):
        """
        A convienience filter for date-based filters such as "created in the
        last 24hrs". Uses the `created_at` column by default but can be
        pointed to any datetime column.

        Options for `cutoff` are 'hour', 'day', 'week', 'month', and 'year'
        """
        current_time = now()
        if cutoff == "hour":
            cutoff_date = current_time - timedelta(hours=1)
        elif cutoff == "day":
            cutoff_date = current_time - timedelta(days=1)
        elif cutoff == "week":
            cutoff_date = current_time - timedelta(days=7)
        elif cutoff == "month":
            cutoff_date = current_time - timedelta(days=30)
        elif cutoff == "year":
            cutoff_date = current_time - timedelta(days=365)
        else:
            raise Exception(f"Unknown age cutoff: {cutoff}")

        return self.filter(**{f"{age_column}__gte": cutoff_date})

    def count_by_column(self, column: str) -> dict:
        """
        Util to count the rows per column. Meant for ChoiceField columns such
        as "status" where you want to know how many of each there are.
        """
        result = self.values(column).annotate(count=models.Count(column))
        return {entry[column]: entry["count"] for entry in result}


# Copied this line from...
# https://github.com/chrisdev/django-pandas/blob/master/django_pandas/managers.py
# It simply converts this queryset class to a manager.
DatabaseTableManager = models.Manager.from_queryset(SearchResults)
