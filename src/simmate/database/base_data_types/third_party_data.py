# -*- coding: utf-8 -*-


class ThirdPartyData:
    """
    A mixin for database tables that ingest data from third-party sources.
    This provides fields and methods for tracking the source of the data,
    citing it, and loading it from remote archives.
    """

    source_doi: str = None
    """
    Source paper that must be referenced if this data is used. If this is None,
    please refer to the `source` attribute for further details on what to 
    reference.
    """

    external_website: str = None
    """
    The homepage of the source website, if the data is loaded from a third-party
    """

    remote_archive_link: str = None
    """
    The URL that is used to download the archive and then populate this table.
    Many tables have pre-existing data that you can download and load into 
    your local database, so if this attribute is set, you can use the 
    `load_remote_archive` method.
    """

    is_redistribution_allowed: bool = True
    """
    Whether this data can be redistribution by the Simmate team. This is used
    to control whether the data is shown in the website's data explorer or
    if it can be downloaded via `load_remote_archive`.
    """

    @property
    def external_link(self) -> str:
        """
        The URL to the specific entry on the source website. By default, this
        simply returns the `external_website` attribute.
        """
        return self.external_website
