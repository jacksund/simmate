# -*- coding: utf-8 -*-

import platform

import numpy
import pandas
import pyodbc

# INSTALLATION NOTE:
# the driver must be install separately from pyodbc!
# https://learn.microsoft.com/en-us/sql/connect/python/pyodbc/python-sql-driver-pyodbc


class MsSqlDB:
    """
    This class helps handle database connections to a Microsoft Server SQL database.
    We also include common queries as preset methods for quick access to raw data.

    You typically don't use this class directly, but instead use one of it's
    subclasses.

    Moreover, these subclasses are only meant if you want raw data! More often
    than not, you likely want to access data in the Simmate database instead,
    which has been cleaned and standardized.
    """

    server: str = None
    """
    SERVER where the databases exists (e.g. somesite.com)
    Note, the "SERVER" is also referred to as the "host".
    """

    port: int = None
    """
    Port that the host accepts tcp connections on (e.g. 1433)
    """

    database: str = None
    """
    The service name (aka database name) to connect to
    """

    user: str = None
    """
    The default username to connect to this database with
    """

    password: str = None
    """
    The default password to connect to this database with
    """

    def __init__(
        self,
        user: str = None,
        password: str = None,
        driver_lib: str = None,
    ):
        """
        Initializes the database connection and a cursor to query with
        """
        if not user:
            user = self.user
        if not password:
            password = self.password
        if not user or not password:
            raise Exception(
                "To connect to this database, you must provide a username and "
                "password either as kwargs or set them using the "
                f"{self.user_env_var} and {self.password_env_var} "
                "evironment variables."
            )

        if not driver_lib:
            system = platform.system()
            if system == "Windows":
                driver_lib = "{ODBC Driver 18 for SQL Server}"
            elif system == "Linux":
                driver_lib = "/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so"
            else:
                raise Exception("You must set 'driver_lib' for MS-SQL connections")

        config = {
            "DRIVER": driver_lib,
            "SERVER": self.server,  # aka the HOST
            "DATABASE": self.database,
            "PORT": self.port,
            "UID": user,
            "PWD": password,
            "TrustServerCertificate": "yes",
            "ENCRYPT": "yes",
            "TDS_Version": "7.3",
        }

        self.config_str = ";".join([f"{k}={v}" for k, v in config.items()])
        self.connection = pyodbc.connect(self.config_str)
        self.cursor = self.connection.cursor()

    def get_query_data(self, query: str) -> pandas.DataFrame:
        """
        Given an SQL query, this will call 'fetchall' and return the results
        as a pandas dataframe.
        """
        # TODO: consider supporting different query types (e.g. COUNT)
        # fetchall, fetchmany (+ chunksize), fetch (i.e. chunksize = 1)
        # fetch_type: str = "fetchall",
        # chunk_size: str = None,
        self.cursor.execute(query)

        data = pandas.DataFrame(
            # BUG: for some reason I need to convert the list of Tuples to
            # a list of lists for pandas to read this successfully...
            data=[list(e) for e in self.cursor.fetchall()],
            columns=[c[0] for c in self.cursor.description],
        )
        # ---- BUG FIXES -----------------------
        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})
        # This line is needed if we have fetch_lobs=True
        # df.COMPOUND_MOLFILE = df.COMPOUND_MOLFILE.apply(str)
        # --------------------------------------
        return data
