# -*- coding: utf-8 -*-

import numpy
import pandas
import requests
from trino.auth import JWTAuthentication, OAuth2Authentication
from trino.dbapi import connect


class TrinoDB:
    """
    This class helps handle database connections to trino databases.
    We also include common queries as preset methods for quick access to raw data.

    You typically don't use this class directly, but instead use one of it's
    subclasses:

    - LakehouseConnection

    Moreover, these subclasses are only meant if you want raw data! More often
    than not, you likely want to access data in the Simmate database instead,
    which has been cleaned and standardized.
    """

    host: str = None
    """
    Host where the databases exists (e.g. somesite.com)
    """

    port: int = None
    """
    Port that the host accepts tcp connections on (e.g. 5432)
    """

    # ------------------------------------------------------
    # Settings below are only for non-interactive auth
    # ------------------------------------------------------

    tenant_id: str = None

    client_id: str = None

    client_secret: str = None

    scope: str = None

    def __init__(
        self,
        auth_type: str = "JWT",  # or 'OAuth2' to have it open your browser to auth
        client_id: str = None,
        client_secret: str = None,
    ):
        """
        Initializes the database connection and a cursor to query with, while
        also applying patch fixes for encoding errors commonly found in old
        databases.
        """
        if not client_id:
            client_id = self.client_id
        if not client_secret:
            client_secret = self.client_secret

        # configure auth variable
        if auth_type == "JWT":

            # grab an access token
            res = requests.post(
                f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            access_token = res.json()["access_token"]
            auth = JWTAuthentication(access_token)
        elif auth_type == "OAuth2":
            auth = OAuth2Authentication()
        else:
            raise Exception(f"Unknown auth_type: {auth_type}")

        self.connection = connect(
            host=self.host,
            port=self.port,
            auth=auth,
            http_scheme="https",
        )
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
            data=self.cursor.fetchall(),
            columns=[c[0] for c in self.cursor.description],
        )
        # ---- BUG FIXES -----------------------
        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})
        # This line is needed if we have fetch_lobs=True
        # df.COMPOUND_MOLFILE = df.COMPOUND_MOLFILE.apply(str)
        # --------------------------------------
        return data
