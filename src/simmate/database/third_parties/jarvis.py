# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class JarvisStructure(Structure):
    """
    Crystal structures from the [JARVIS](https://jarvis.nist.gov/) database.

    Currently, this table only stores strucure and reported energy above hull.
    The calculated energy is not reported, so the Thermodynamics mixin is not used.
    """

    # Make sure Django knows which app this is associated with
    class Meta:
        app_label = "third_parties"

    base_info = ["id", "structure_string", "energy_above_hull"]
    """
    The base information for this database table. All other columns can be calculated
    using the columns in this list.
    """

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "jvasp-12345")
    """

    source = "JARVIS"
    """
    Where this structure and data came from.
    """

    source_doi = "https://doi.org/10.1038/s41524-020-00440-1"
    """
    Source paper that must be referenced if this dataset is used.
    """

    # TODO: contact their team to ask about reporting energy instead. That way
    # we can use the Thermodynamics mixin instead of manually listing this.
    energy_above_hull = table_column.FloatField(blank=True, null=True)
    """
    The energy above hull, as reported by the JARVIS database (no units given)
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the JARVIS website.
        """
        # All JARVIS structures have their data mapped to a URL in the same way
        # ex: https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/JVASP-1234.xml
        # we store the id as "jvasp-123" so we need to convert this to uppercase
        id = self.id.upper()
        return f"https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/{id}.xml"
