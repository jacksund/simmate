# -*- coding: utf-8 -*-

import platform

import numpy
import oracledb
import pandas

from simmate.configuration import settings


class OracleDB:
    """
    This class helps handle database connections to oracle databases.
    These databases typically contain encoding errors which this class
    patches for you. We also include common queries as preset methods for quick
    access to raw data.

    You typically don't use this class directly, but instead use one of it's
    subclasses.

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

    service: str = None
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
        # !!! default below should be `settings.oracle_client_lib` but I don't
        # have a way to add extra defaults to the Simmate settings yet
        client_lib: str = settings.final_settings.get("oracle_client_lib"),
    ):
        """
        Initializes the database connection and a cursor to query with, while
        also applying patch fixes for encoding errors commonly found in old
        databases.
        """
        if not user:
            user = self.user
        if not password:
            password = self.password
        if not user or not password:
            raise Exception(
                "To connect to this database, you must provide a username and "
                "password either as kwargs or set them using the "
                f"{self.username_env_var} and {self.password_env_var} "
                "evironment variables."
            )

        if platform.system() == "Windows" and not client_lib:
            raise Exception(
                "This db does not support connections in thin mode, so you need "
                "install the 'Basic' oracle client and then use the 'client_lib' input "
                "parameter to tell Simmate where it's installed. Download from here: "
                "https://www.oracle.com/database/technologies/instant-client.html"
            )
        elif platform.system() == "Windows" and client_lib:
            oracledb.init_oracle_client(lib_dir=client_lib)
        elif platform.system() == "Linux":
            oracledb.init_oracle_client()  # dir detected automatically on linux

        # return LOBs directly as strings or bytes
        oracledb.defaults.fetch_lobs = False

        self.dsn = oracledb.makedsn(
            host=self.host,
            port=self.port,
            service_name=self.service,  # aka "database"
        )
        self.connection = oracledb.connect(
            user=user,
            password=password,
            dsn=self.dsn,
        )
        self.cursor = self.connection.cursor()

        # setup cursor for old db bug-fix
        self._patch_cursor(self.cursor)

    def get_query_data(self, query: str, fetch_size: int = 1_000) -> pandas.DataFrame:
        """
        Given an SQL query, this will call 'fetchall' and return the results
        as a pandas dataframe.
        """
        # TODO: consider supporting different query types (e.g. COUNT)
        # fetchall, fetchmany (+ chunksize), fetch (i.e. chunksize = 1)
        # fetch_type: str = "fetchall",
        # chunk_size: str = None,
        self.cursor.execute(query)

        # below is the same as...
        #   self._patch_fetch(self.cursor.fetchall())
        # But fetching 1,000 at a time is more stable and often faster
        fetch_data = []
        new_data = True
        while new_data:
            new_data = self._patch_fetch(self.cursor.fetchmany(fetch_size))
            fetch_data += new_data

        data = pandas.DataFrame(
            data=fetch_data,
            columns=[c[0] for c in self.cursor.description],
        )
        # ---- BUG FIXES -----------------------
        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})
        # This line is needed if we have fetch_lobs=True
        # df.COMPOUND_MOLFILE = df.COMPOUND_MOLFILE.apply(str)
        # --------------------------------------
        return data

    @staticmethod
    def _patch_cursor(cursor: oracledb.Cursor):
        """
        The encoding is messed up in several legacy databases where UTF-8 or
        anything else we try setting as fails -- probably bc there are
        multiple encoding types in the database.

        So what we do is tell oracle to NOT decode the bytes pass, and instead
        try decoding bytes to strings later (see _patch_fetch method).

        Fix recommended by:
         - https://cx-oracle.readthedocs.io/en/latest/user_guide/sql_execution.html#fetching-raw-data
        """

        # This fxn is copied from the recommended code.
        def _return_strings_as_bytes(
            cursor,
            name,
            default_type,
            size,
            precision,
            scale,
        ):
            if default_type == oracledb.DB_TYPE_VARCHAR:
                return cursor.var(
                    str,
                    arraysize=cursor.arraysize,
                    bypass_decode=True,
                )

        cursor.outputtypehandler = _return_strings_as_bytes

    @staticmethod
    def _patch_fetch(fetchall_data: list) -> list:
        """
        The _patch_cursor method returns buggy encodings back as bytes.
        Here, we try to convert them to strings using different
        encodings.

        For devs... The following SQL can grab other potential encodings to try:
        ``` sql
        select distinct utl_i18n.map_charset(value)
        from v$nls_valid_values
        where parameter = 'CHARACTERSET'
            and utl_i18n.map_charset(value) is not null
        order by 1
        ```
        """
        data_cleaned = []
        for entry in fetchall_data:
            entry = list(entry)
            for value_index, value in enumerate(entry):
                if not isinstance(value, bytes):
                    continue
                is_decoded = False
                for encoding in [
                    # "UTL_I18N.MAP_CHARSET(VALUE)",
                    # "BIG5",
                    # "BIG5-HKSCS",
                    # "CP00858",
                    # "CP00924",
                    # "CP01140",
                    # "CP01141",
                    # "CP01142",
                    # "CP01143",
                    # "CP01144",
                    # "CP01145",
                    # "CP01146",
                    # "CP01147",
                    # "CP01148",
                    # "CP037",
                    # "CP1026",
                    # "CP273",
                    # "CP278",
                    # "CP280",
                    # "CP284",
                    # "CP285",
                    # "CP297",
                    # "CP420",
                    # "CP423",
                    # "CP424",
                    # "CP437",
                    # "CP500",
                    # "CP775",
                    # "CP850",
                    # "CP851",
                    # "CP852",
                    # "CP855",
                    # "CP857",
                    # "CP860",
                    # "CP861",
                    # "CP862",
                    # "CP863",
                    # "CP865",
                    # "CP866",
                    # "CP869",
                    # "CP870",
                    # "CP871",
                    # "DEC-MCS",
                    # "DIN_66003",
                    # "ES",
                    # "EUC-JP",
                    # "EUC-KR",
                    # "GB18030",
                    # "GBK",
                    # "HP-ROMAN8",
                    # "IBM1047",
                    # "IBM277",
                    # "ISO-8859-1",
                    # "ISO-8859-10",
                    # "ISO-8859-13",
                    # "ISO-8859-14",
                    # "ISO-8859-15",
                    # "ISO-8859-2",
                    # "ISO-8859-3",
                    # "ISO-8859-4",
                    # "ISO-8859-5",
                    # "ISO-8859-6",
                    # "ISO-8859-7",
                    # "ISO-8859-8-I",
                    # "ISO-8859-9",
                    # "IT",
                    # "JUS_I.B1.002",
                    # "KOI8-R",
                    # "KOI8-U",
                    # "MACINTOSH",
                    # "NF_Z_62-010_(1973)",
                    # "NS_4551-1",
                    # "SEN_850200_B",
                    # "SEN_850200_C",
                    # "SHIFT_JIS",
                    # "TIS-620",
                    # "US-ASCII",
                    # "UTF-16BE",
                    "UTF-8",
                    "WINDOWS-1250",
                    # "WINDOWS-1251",
                    # "WINDOWS-1252",
                    # "WINDOWS-1253",
                    # "WINDOWS-1254",
                    # "WINDOWS-1255",
                    # "WINDOWS-1256",
                    # "WINDOWS-1257",
                    # "WINDOWS-1258",
                ]:
                    try:
                        value_cleaned = value.decode(encoding)
                        entry[value_index] = value_cleaned
                        is_decoded = True
                        break
                    except:
                        pass
                if not is_decoded:
                    raise Exception(f"Failed to decode bytes: {value}")
            data_cleaned.append(entry)
        return data_cleaned
