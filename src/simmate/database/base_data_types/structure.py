# -*- coding: utf-8 -*-

from django.db.models import Func
from scipy.constants import Avogadro

from simmate.configuration import settings
from simmate.database.base_data_types import (
    DatabaseTable,
    SearchResults,
    Spacegroup,
    table_column,
)
from simmate.toolkit import Structure as ToolkitStructure
from simmate.toolkit.validators.fingerprint import PartialCrystalNNFingerprint
from simmate.utilities import get_chemical_subsystems


# UNDER DEV -- Not used elsewhere yet
class StructureSearchResults(SearchResults):

    def filter_similarity(
        self,
        structure: ToolkitStructure,
        method: str = "L2",
        cutoff: float = 0.8,
        order: bool = True,
    ):
        """
        Method for searching table for matching structures using the pgvector
        extension in postgres databases. If another backend is used, the search
        manually calculates the distance using scipy which is much slower for
        methods running on parallel machines (i.e. evolutionary search) as it
        must be run locally rather than on the host server (requiring the fingerprints
        to be transferred to the local cpu).
        """
        #############################################
        NotImplementedError("Method still in testing")
        #############################################

        if settings.database_backend != "postgresql":
            NotImplementedError(
                "Similarity searches in-database are not supported outside of "
                "postgres. You can still use the toolkit's SimilarityFilter "
                "to handle this outside the database though."
            )
            # TODO: may remove and just require users to switch to postgres, so
            # I'd like to leave this disabled for now

            # Sam's method which will be converted to a filter:
            # if method == "L2":
            #     scipy_method_str = "euclidean"
            # elif method == "inner product":
            #     scipy_method_str = "inner product" # This is easier to implement with numpy
            # elif method == "cosine":
            #     scipy_method_str = "cosine"
            # elif method == "L1":
            #     scipy_method_str = "cityblock"
            # elif method == "hamming":
            #     scipy_method_str = "hamming"
            # elif method == "jaccard":
            #     scipy_method_str = "jaccard"
            # # our database backend is not postgress. We calculate the distance
            # # locally using numpy/scipy instead of pgvector
            # fingerprints = cls.objects.values_list("fingerprint", flat=True)
            # fingerprints_array = np.vstack(fingerprints)
            # if scipy_method_str == "inner product":
            #     # no inner product method for cdist, but it's easy to do with numpy
            #     # note this distance is higher for closer arrays and is dependent
            #     # on magnitude of the vectors.
            #     distances = -np.dot(fingerprints_array, new_fingerprint)
            # else:
            #     reshaped_new_fingerprint = new_fingerprint.reshape(1,-1) # reshape because scipy requires 2D
            #     distances = cdist(fingerprints_array, reshaped_new_fingerprint, metric=scipy_method_str)
            # result_indices = np.where(distances<cutoff)[0]
            # if len(result_indices) > 0:
            #     # return datatable id for structures that match
            #     db_ids = [cls.objects.values_list("id", flat=True)[int(i)] for i in result_indices]
            #     return db_ids

        # BUG:
        # This doesn't check if pgvector is installed. Is there a way to do this? -@SWeav02
        #
        # Yes, there is a way to enforce this, which is what I do with Rdkit+postgres,
        # but it may result in us *requiring* postgres and doing away with sqlite
        # altogether. I'll think more on a workaround -@jacksund

        # from name to pgvector op
        operator_mappings = {
            "L1": "<+>",  # cityblock
            "L2": "<->",  # euclidean
            "inner product": "<#>",
            "cosine": "<=>",
            "hamming": "<~>",
            "jaccard": "<%>",
        }
        if method not in operator_mappings:
            raise Exception(
                f"{method} is not implemented as a distance metric. "
                f"Available options are L2, inner product, cosine, L1, hamming, and jaccard."
            )

        if not isinstance(structure, ToolkitStructure):
            structure = ToolkitStructure.from_dynamic(structure)

        # get new structure feature
        featurizer = PartialCrystalNNFingerprint.get_featurizer(
            composition=structure.composition
        )
        new_fingerprint = featurizer.featurize(structure)
        fingerprint_str = str(new_fingerprint)
        # TODO: this is used in several places and should probably be a property
        # of our toolkit structure class

        queryset = self.annotate(
            similarity=Func(
                "fingerprint_crystalnn",  # the column that holds the fingerprint
                reference_structure=fingerprint_str,
                function="tanimoto_sml",
                template="...",  # TODO
                output_field=table_column.FloatField(),
            )
        )
        # This code below does the same thing & is easier to read -- but it doesn't
        # allow for use of filter() afterwards, so we opt for the annotate()
        # method above.
        #
        # BUG: injection risk here.
        #   https://docs.djangoproject.com/en/4.2/topics/db/sql/#passing-parameters-into-raw
        #
        # NOTE: the percent signs are doubled in this query, when the real
        # SQL query they are single! This is because django tries to read
        # them as a formatted string
        #
        # query = (
        #       TODO
        # )
        # results = cls.objects.raw(query)

        # Sam's query template:
        # SELECT * FROM fingerprint WHERE embedding {postgres_method_str} '{fingerprint_str}' < {cutoff};
        # FROM {table_name}

        if cutoff:
            queryset = queryset.filter(
                similarity__gte=cutoff,
            )

        if order:
            # reverse order because bigger number = more similar
            queryset = queryset.order_by("-similarity_2d")

        return queryset


class Structure(DatabaseTable):
    class Meta:
        abstract = True

    exclude_from_summary = ["structure", "elements"]

    archive_fields = ["structure"]

    # NOTE: below is for legacy implementation of compositional API searches.
    # This is kept for reference as we migrate to the new api
    #
    # from django_filters import rest_framework as django_api_filters
    # # Whether to include subsystems of the given `chemical_system`. For
    # # example, the subsystems of Y-C-F would be Y, C, F, Y-C, Y-F, etc..
    # include_subsystems=django_api_filters.BooleanFilter(
    #     field_name="include_subsystems",
    #     label="Include chemical subsystems in results?",
    #     method="skip_filter",
    # ),
    # # TODO: Supra-systems would include all the elements listed AND more. For example,
    # # searching Y-C-F would also return Y-C-F-Br, Y-Sc-C-F, etc.
    # # include_suprasystems = forms.BooleanField(label="Include Subsytems", required=False)
    # # The chemical system of the structure (e.g. "Y-C-F" or "Na-Cl")
    # chemical_system=django_api_filters.CharFilter(
    #     method="filter_chemical_system",
    # )

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

    # TODO:
    # fingerprint_crystalnn = table_column.JSONField(blank=True, null=True)
    # """
    # The fingerprint for the structure determined using a custom CrystalNN fingerprint
    # """
    # TODO: This should be a vector type column to be most efficient. Otherwise
    # the database will run conversions on the entire column before doing distance
    # comparisons -- which would be a clear bottleneck.

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

    # DEPRECIATED: will move to `StructureSearchResults`
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
        # if there isn't a structure, nothing is to be done.
        if not structure:
            return kwargs if as_dict else cls(**kwargs)

        if isinstance(structure, str):
            structure = ToolkitStructure.from_database_string(structure)

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

        # TODO:
        # Generate fingerprint
        # featurizer = PartialCrystalNNFingerprint.get_featurizer(
        #     composition=structure.composition
        # )
        # fingerprint = featurizer.featurize(structure)

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
            # fingerprint_crystalnn=list(fingerprint),
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
