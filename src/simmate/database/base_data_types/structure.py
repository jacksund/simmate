# -*- coding: utf-8 -*-

from scipy.constants import Avogadro

from simmate.toolkit import Structure as ToolkitStructure
from simmate.database.base_data_types import (
    DatabaseTable,
    table_column,
    Spacegroup,
)


class Structure(DatabaseTable):
    class Meta:
        abstract = True

    base_info = ["structure_string"]

    structure_string = table_column.TextField(blank=True, null=True)
    """
    The core structure information, which is written to a string and in a 
    compressed format using the `from_toolkit` method. To get back to our toolkit
    structure object, use the `to_toolkit` method.
    """

    nsites = table_column.IntegerField(blank=True, null=True)
    """
    The total number of sites in the unitcell. (e.g. Y2CF2 has 5 sites)
    """

    nelements = table_column.IntegerField(blank=True, null=True)
    """
    The total number of unique elements. (e.g. Y2CF2 has 3 elements)
    """

    elements = table_column.JSONField(blank=True, null=True)
    """
    List of elements in the structure (ex: ["Y", "C", "F"])
    """

    chemical_system = table_column.CharField(max_length=25, blank=True, null=True)
    """
    the base chemical system (ex: "Y-C-F")
    
    Note: be careful when searching for elements! Running chemical_system__contains="C"
    on this field won't do what you expect -- because it will return structures
    containing Ca, Cs, Ce, Cl, and so on. If you want to search for structures
    that contain a specific element, use elements__contains='"C"' instead. The
    odd use of quotes '"C"' is required here!
    """

    density = table_column.FloatField(blank=True, null=True)
    """
    The density of the crystal in g/cm^3
    """

    density_atomic = table_column.FloatField(blank=True, null=True)
    """
    The density of atoms in the crystal in atoms/Angstom^3
    """

    volume = table_column.FloatField(blank=True, null=True)
    """
    The volume of the unitcell in Angstom^3
    
    Note: in most cases, `volume_molar` should be used instead! This is because
    volumne is highly dependent on the symmetry and the arbitray unitcell. If 
    you are truly after small volumes of the unitcell, it is likely you really 
    just want to search by spacegroup.
    """

    volume_molar = table_column.FloatField(blank=True, null=True)
    """
    The molar volume of the crystal in cm^3/mol
    """

    # The composition of the structure formatted in various ways
    # BUG: The max length here is overkill because there are many structures
    # with 8+ elements and disordered formula (e.g. "Ca2.103 N0.98")

    formula_full = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    """
    The chemical formula with elements sorted by electronegativity (ex: Li4 Fe4 P4 O16)
    """

    formula_reduced = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    """
    The reduced chemical formula. (ex: Li4Fe4P4O16 --> LiFePO4)
    """

    formula_anonymous = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    """
    An anonymized formula. Unique species are arranged in ordering of 
    amounts and assigned ascending alphabets. Useful for prototyping formulas. 
    For example, all stoichiometric perovskites have anonymized_formula ABC3.
    """

    spacegroup = table_column.ForeignKey(
        Spacegroup,
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
    )
    """
    Spacegroup information. Points to a separate database table that has additional
    columns:
    `simmate.database.base_data_types.symmetry.Spacegroup`
    """

    # The AFLOW prototype that this structure maps to.
    # TODO: this will be a relationship in the future
    # prototype = table_column.CharField(max_length=50, blank=True, null=True)

    # NOTE: extra fields for the Lattice and Sites are intentionally left out
    # in order to save on overall database size. Things such as...
    #   Lattice: matrix and then... a, b, c, alpha, beta, gamma, volume
    #   Sites: abc, xyz, properties, species/element, occupancy
    # shouldn't be queried directly. If you'd like to sort structures by these
    # criteria, you can still do this in python and pandas! Just not at the
    # SQL level

    @classmethod
    def _from_toolkit(
        cls,
        structure: ToolkitStructure,
        as_dict: bool = False,
        **kwargs,
    ):

        # BUG: This is an old line and I can't remember why I have it. Once I
        # have implemented more unittests, consider deleting. This method is
        # ment to convert to a ToolkitStructure, but the structure should
        # already be in this format...
        structure = ToolkitStructure.from_dynamic(structure)

        # OPTIMIZE: I currently store files as poscar strings for ordered structures
        # and as CIFs for disordered structures. Both of this include excess information
        # that slightly inflates file size, so I will be making a new string format in
        # the future. This will largely be based off the POSCAR format, but will
        # account for disordered structures and all limit repeated data (such as the
        # header line, "direct", listing each element/composition, etc.).
        storage_format = "POSCAR" if structure.is_ordered else "CIF"

        # OPTIMIZE
        # This attempts to match the structure to an AFLOW prototype and it is
        # by far the slowest step of loading structures to the database. Try
        # to optimize this in the future.
        # from pymatgen.analysis.prototypes import AflowPrototypeMatcher
        # prototype = AflowPrototypeMatcher().get_prototypes(structure)
        # prototype_name = prototype[0]["tags"]["mineral"] if prototype else None

        # Given a pymatgen structure object, this will return a database structure
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields.
        structure_dict = dict(
            structure_string=structure.to(fmt=storage_format),
            nsites=structure.num_sites,
            nelements=len(structure.composition),
            elements=[str(e) for e in structure.composition.elements],
            chemical_system=structure.composition.chemical_system,
            density=structure.density,
            density_atomic=structure.num_sites / structure.volume,
            volume=structure.volume,
            # 1e-27 is to convert from cubic angstroms to Liter and then 1e3 to
            # mL. Therefore this value is in mL/mol
            # OPTIMIZE: move this to a class method
            volume_molar=(structure.volume / structure.num_sites)
            * Avogadro
            * 1e-27
            * 1e3,
            spacegroup_id=structure.get_space_group_info()[1],  # OPTIMIZE
            formula_full=structure.composition.formula,
            formula_reduced=structure.composition.reduced_formula,
            formula_anonymous=structure.composition.anonymized_formula,
            # prototype=prototype_name,
            **kwargs,  # this allows subclasses to add fields with ease
        )
        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return structure_dict if as_dict else cls(**structure_dict)

    def to_toolkit(self) -> ToolkitStructure:
        """
        Converts the database object to toolkit Structure object.
        """
        return ToolkitStructure.from_database_object(self)
