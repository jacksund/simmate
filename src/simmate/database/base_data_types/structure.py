# -*- coding: utf-8 -*-

from django_filters import rest_framework as django_api_filters
from scipy.constants import Avogadro

from simmate.database.base_data_types import DatabaseTable, Spacegroup, table_column
from simmate.toolkit import Structure as ToolkitStructure
from simmate.utilities import get_chemical_subsystems


class Structure(DatabaseTable):
    class Meta:
        abstract = True

    exclude_from_summary = ["structure", "elements"]

    archive_fields = ["structure"]

    api_filters = dict(
        nsites=["range"],
        nelements=["range"],
        # elements=["contains"],
        density=["range"],
        density_atomic=["range"],
        volume=["range"],
        volume_molar=["range"],
        formula_full=["exact"],
        formula_reduced=["exact"],
        formula_anonymous=["exact"],
        spacegroup__number=["exact"],
        spacegroup__symbol=["exact"],
        spacegroup__crystal_system=["exact"],
        spacegroup__point_group=["exact"],
        # Whether to include subsystems of the given `chemical_system`. For
        # example, the subsystems of Y-C-F would be Y, C, F, Y-C, Y-F, etc..
        include_subsystems=django_api_filters.BooleanFilter(
            field_name="include_subsystems",
            label="Include chemical subsystems in results?",
            method="skip_filter",
        ),
        # TODO: Supra-systems would include all the elements listed AND more. For example,
        # searching Y-C-F would also return Y-C-F-Br, Y-Sc-C-F, etc.
        # include_suprasystems = forms.BooleanField(label="Include Subsytems", required=False)
        # The chemical system of the structure (e.g. "Y-C-F" or "Na-Cl")
        chemical_system=django_api_filters.CharFilter(
            method="filter_chemical_system",
        ),
    )

    structure = table_column.TextField(blank=True, null=True)
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

    def filter_chemical_system(self, queryset, name, value):
        # name/value here are the key/value pair for chemical system

        # Grab the "include_subsystems" field from the filter form. Note, this
        # value will be given as a string which we convert to a python boolean
        include_subsystems = self.data.dict().get("include_subsystems", "false")
        include_subsystems = True if include_subsystems == "true" else False

        # TODO:
        # Make sure that the chemical system is made of valid elements and
        # separated by hyphens

        # check if the user wants subsystems included (This will be True or False)
        if include_subsystems:
            systems_cleaned = get_chemical_subsystems(value)

        # otherwise just clean the single system
        else:
            # Convert the system to a list of elements
            systems_cleaned = value.split("-")
            # now recombine the list back into alphabetical order
            systems_cleaned = ["-".join(sorted(systems_cleaned))]
            # NOTE: we call this "systems_cleaned" and put it in a list so
            # that our other methods don't have to deal with multiple cases
            # when running a django filter.

        filtered_queryset = queryset.filter(chemical_system__in=systems_cleaned)

        # now return the cleaned value. Note that this is now a list of
        # chemical systems, where all elements are in alphabetical order.
        return filtered_queryset

    @classmethod
    def _from_toolkit(
        cls,
        structure: ToolkitStructure | str = None,
        as_dict: bool = False,
        **kwargs,
    ):

        if isinstance(structure, str):
            structure = ToolkitStructure.from_database_string(structure)

        # if there isn't a structure, nothing is to be done.
        if not structure:
            return kwargs if as_dict else cls(**kwargs)

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
        # Alternatively, add as a method to the table, similar to
        # the "update_all_stabilities" for thermodynamics

        # Given a pymatgen structure object, this will return a database structure
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields.
        structure_dict = dict(
            structure=structure.to(fmt=storage_format),
            nsites=structure.num_sites,
            nelements=len(structure.composition),
            elements=[str(e) for e in structure.composition.elements],
            chemical_system=structure.composition.chemical_system,
            density=float(structure.density),
            density_atomic=structure.num_sites / structure.volume,
            volume=structure.volume,
            # 1e-27 is to convert from cubic angstroms to Liter and then 1e3 to
            # mL. Therefore this value is in mL/mol
            # OPTIMIZE: move this to a class method
            volume_molar=(structure.volume / structure.num_sites)
            * Avogadro
            * 1e-27
            * 1e3,
            # OPTIMIZE SPACEGROUP INFO
            spacegroup_id=structure.get_space_group_info(
                symprec=0.1,
                # angle_tolerance=5.0,
            )[1],
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
