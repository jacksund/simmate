# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class CodStructure(Structure):
    """
    Crystal structures from the [COD](http://www.crystallography.net/cod/) database.

    Currently, this table only stores the strucure, plus comments on whether the
    sturcture is ordered or has implicit hydrogens.
    """

    class Meta:
        app_label = "third_parties"

    base_info = ["id", "structure_string", "is_ordered", "has_implicit_hydrogens"]
    source = "The Crystallography Open Database"
    source_doi = "https://doi.org/10.1107/S0021889809016690"
    remote_archive_link = "https://archives.simmate.org/CodStructure-2022-02-20.zip"

    # These fields overwrite the default Structure fields due to a bug.
    chemical_system = table_column.TextField()
    formula_full = table_column.TextField()
    formula_reduced = table_column.TextField()
    formula_anonymous = table_column.TextField()
    # BUG: We can't use CharField for the COD database because there are a number
    # of structures that have 20+ elements in them and are disordered. The disordered
    # aspect throws issues in pymatgen where formulas can be returned as long
    # floats (ex: Ca2.1234567N). Until this is fixed and cleaned up, I'll
    # need to use TextField instead of CharField for these fields.

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "cod-12345")
    """

    is_ordered = table_column.BooleanField()
    """
    whether the structure contains disordered sites (i.e. mixed occupancies)
    """

    has_implicit_hydrogens = table_column.BooleanField()
    """
    whether the structure has implicit Hydrogens. This means there should be
    Hydrogens in the structure, but they weren't explicitly drawn. Note,
    implicit hydrogens will make the chemical system and formula misleading 
    because of the absence of hydrogens.
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the COD website.
        """
        # All COD structures have their data mapped to a URL in the same way
        # ex: http://www.crystallography.net/cod/12345.html"
        # we store the id as "cod-123" so we need to convert this to uppercase
        id_formatted = self.id.split("-")[-1]
        return f"http://www.crystallography.net/cod/{id_formatted}.html"
