import time

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

    source: str = None
    """
    Client name sent with each query (e.g. "my-app"). If None, the trino
    client's default is used.
    """

    # ------------------------------------------------------
    # Settings below are only for non-interactive auth
    # ------------------------------------------------------

    tenant_id: str = None

    client_id: str = None

    client_secret: str = None

    scope: str = None

    token_refresh_margin: int = 300
    """
    Seconds before the access token expires that a new one is requested. This
    is also the least time a query has before its token expires.
    """

    _access_token: str = None

    _token_expires_at: float = 0

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
        if client_id:
            self.client_id = client_id
        if client_secret:
            self.client_secret = client_secret

        # configure auth variable
        if auth_type == "JWT":
            # the access token is fetched (and refreshed) as queries are made
            self.auth = None
        elif auth_type == "OAuth2":
            self.auth = OAuth2Authentication()
        else:
            raise Exception(f"Unknown auth_type: {auth_type}")

    def get_access_token(self) -> str:
        """
        Gives an access token for non-interactive (JWT) auth, reusing the
        previous one until shortly before it expires.
        """
        if time.time() < self._token_expires_at - self.token_refresh_margin:
            return self._access_token

        res = requests.post(
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )
        token_data = res.json()
        self._access_token = token_data["access_token"]
        # `expires_in` is in seconds (typically ~1 hour)
        self._token_expires_at = time.time() + float(token_data.get("expires_in", 0))
        return self._access_token

    def get_query_data(self, query: str) -> pandas.DataFrame:
        """
        Given an SQL query, this will call 'fetchall' and return the results
        as a pandas dataframe.
        """
        # TODO: consider supporting different query types (e.g. COUNT)
        # fetchall, fetchmany (+ chunksize), fetch (i.e. chunksize = 1)
        # fetch_type: str = "fetchall",
        # chunk_size: str = None,

        connect_kwargs = dict(source=self.source) if self.source else {}
        with (
            connect(
                host=self.host,
                port=self.port,
                auth=self.auth or JWTAuthentication(self.get_access_token()),
                http_scheme="https",
                **connect_kwargs,
            ) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(query)
            data = pandas.DataFrame(
                data=cursor.fetchall(),
                columns=[c[0] for c in cursor.description],
            )

        # ---- BUG FIXES -----------------------
        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})
        # This line is needed if we have fetch_lobs=True
        # df.COMPOUND_MOLFILE = df.COMPOUND_MOLFILE.apply(str)
        # --------------------------------------
        return data
