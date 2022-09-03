# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, Thermodynamics, table_column


class MatprojStructure(Structure, Thermodynamics):
    """
    Crystal structures from the [Materials Project](https://materialsproject.org/)
    database.

    Currently, this table only stores strucure and thermodynamic information,
    but the Materials Project has much more data available via their
    [REST API](https://github.com/materialsproject/api) and website.
    """

    class Meta:
        app_label = "third_parties"

    archive_fields = [
        "energy_uncorrected",
        "band_gap",
        "is_gap_direct",
        "is_magnetic",
        "total_magnetization",
        "is_theoretical",
    ]
    api_filters = dict(
        energy_uncorrected=["range"],
        band_gap=["range"],
        is_gap_direct=["exact"],
        is_magnetic=["exact"],
        total_magnetization=["range"],
        is_theoretical=["exact"],
    )
    source = "Materials Project"
    source_long = "The Materials Project at Berkeley National Labs"
    homepage = "https://materialsproject.org/"
    source_doi = "https://doi.org/10.1063/1.4812323"
    remote_archive_link = "https://archives.simmate.org/MatprojStructure-2022-08-27.zip"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "mp-12345")
    """

    energy_uncorrected = table_column.FloatField(blank=True, null=True)
    """
    The reported energy of the system BEFORE Materials Project applies
    their composition-based corrections.
    """

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    """
    Whether the band gap is direct or indirect.
    """

    is_magnetic = table_column.BooleanField(blank=True, null=True)
    """
    Whether the material is magnetic
    """

    total_magnetization = table_column.FloatField(blank=True, null=True)
    """
    The total magnetization of the material
    """

    is_theoretical = table_column.BooleanField(blank=True, null=True)
    """
    Whether the material is from a theoretical structure. False indicates
    that it is experimentally known.
    """

    updated_at = table_column.DateTimeField(blank=True, null=True)
    """
    Timestamp of when this row was was lasted changed / updated by the 
    Materials Project
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the Materials Project website.
        """
        # All Materials Project structures have their data mapped to a URL in
        # the same way. For example...
        #   https://materialsproject.org/materials/mp-12345/
        return f"https://materialsproject.org/materials/{self.id}/"
