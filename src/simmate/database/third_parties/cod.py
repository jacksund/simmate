# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class CodStructure(Structure):
    """
    Crystal structures from the [COD](http://www.crystallography.net/cod/) database.

    Currently, this table only stores the strucure, plus comments on whether the
    sturcture is ordered or has implicit hydrogens.
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

    is_ordered = table_column.BooleanField()
    """
    whether the structure contains disordered sites (i.e. mixed occupancies)
    """

    has_implicit_hydrogens = table_column.BooleanField()
    """
    whether the structure has implicit Hydrogens. This means there should be
    Hydrogens in the structure, but they weren't explicitly drawn.
    """

    source = "COD"
    """
    Where this structure and data came from.
    """

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

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the COD website.
        """
        # All COD structures have their data mapped to a URL in the same way
        # ex: https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/JVASP-1234.xml
        # we store the id as "cod-123" so we need to convert this to uppercase
        id_formatted = self.id.split("-")[-1]
        return f"http://www.crystallography.net/cod/{id_formatted}.html"
