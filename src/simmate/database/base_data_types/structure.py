# -*- coding: utf-8 -*-

from scipy.constants import Avogadro

from pymatgen.core.structure import Structure as Structure_PMG

# from pymatgen.analysis.prototypes import AflowPrototypeMatcher

from simmate.database.base_data_types import (
    DatabaseTable,
    table_column,
    Spacegroup,
)


class Structure(DatabaseTable):

    """Base Info"""

    # The structure which is written to a string and in a compressed format
    # using the .from_pymatgen() method. To get back to our pymatgen structure
    # object, use the .to_pymatgen() method!
    structure_string = table_column.TextField()

    """ Query-helper Info """

    # total number of sites in the unitcell
    nsites = table_column.IntegerField()

    # total number of unique elements
    nelements = table_column.IntegerField()

    # List of elements in the structure (ex: ["Y", "C", "F"])
    elements = table_column.JSONField()
    # the base chemical system (ex: "Y-C-F")
    chemical_system = table_column.CharField(max_length=25)
    # Note: be careful when searching for elements! Running chemical_system__includes="C"
    # on this field won't do what you expect -- because it will return structures
    # containing Ca, Cs, Ce, Cl, and so on. If you want to search for structures
    # that contain a specific element, use elements__contains="C" instead.

    # Density of the crystal (g/cm^3)
    density = table_column.FloatField()

    # Density of atoms in the crystal (atoms/Angstom^3)
    density_atomic = table_column.FloatField()

    # Volume of the unitcell.
    # Note: in most cases, volume_molar should be used instead!
    volume = table_column.FloatField()

    # Molar volume of the crystal (cm^3/mol)
    # Note we prefer this over a "volume" field because volume is highly dependent
    # on the symmetry and the arbitray unitcell. If you are truly after small volumes
    # of the unitcell, it is likely you really just want to search by spacegroup.
    volume_molar = table_column.FloatField()

    # The composition of the structure formatted in various ways
    # BUG: The max length here is overkill because there are many structures
    # with 8+ elements and disordered formula (e.g. "Ca2.103 N0.98")
    formula_full = table_column.CharField(max_length=50)  # more
    formula_reduced = table_column.CharField(max_length=50)
    formula_anonymous = table_column.CharField(max_length=50)

    # NOTE: extra fields for the Lattice and Sites are intentionally left out
    # in order to save on overall database size. Things such as...
    #   Lattice: matrix and then... a, b, c, alpha, beta, gamma, volume
    #   Sites: abc, xyz, properties, species/element, occupancy
    # shouldn't be queried directly. If you'd like to sort structures by these
    # criteria, you can still do this in python and pandas! Just not at the
    # SQL level

    """ Relationships """
    # For the majority of Structures, you'll want to have a "source" relation that
    # indicates where the structure came from. I don't include this is the abstract
    # model but there are many ways to define it. For example it may relate to another
    # Structure table or even a Calculation. In another case, the entire Structure
    # table may have the same exact source, in which case you'd make a property!

    # Each structure can have many Calculation(s)

    # symmetry info
    spacegroup = table_column.ForeignKey(Spacegroup, on_delete=table_column.PROTECT)

    # The AFLOW prototype that this structure maps to.
    # TODO: this will be a relationship in the future
    # prototype = table_column.CharField(max_length=50, blank=True, null=True)

    """ Properties """
    # none

    """ Model Methods """

    @classmethod
    def from_pymatgen(cls, structure, as_dict=False, **kwargs):

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
            spacegroup_id=structure.get_space_group_info(0.1)[1],  # OPTIMIZE
            formula_full=structure.composition.formula,
            formula_reduced=structure.composition.reduced_formula,
            formula_anonymous=structure.composition.anonymized_formula,
            # prototype=prototype_name,
            **kwargs,  # this allows subclasses to add fields with ease
        )
        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return structure_dict if as_dict else cls(**structure_dict)

    def to_pymatgen(self):
        # Converts the database object to pymatgen structure object

        # NOTE: if you know this is what you're going to do from a query, then
        # it is more efficient to only grab the structure_string column because
        # that's all you need! You'd do that like this:
        #   structure_db = Structure.objects.only("structure_string").get(id="example-id")
        # This grabs the proper Structure entry and only the structure column.

        # convert the stored string to python dictionary.
        # OPTIMIZE: see my comment on storing strings in the from_pymatgen method above.
        # For now, I need to figure out if I used "CIF" or "POSCAR" and read the structure
        # accordingly. In the future, I can just assume my new format.
        # If the string starts with "#", then I know that I stored it as a "CIF".
        storage_format = "CIF" if (self.structure_string[0] == "#") else "POSCAR"

        # convert the string to pymatgen Structure object
        structure = Structure_PMG.from_str(
            self.structure_string,
            fmt=storage_format,
        )

        return structure

    """ For website compatibility """

    class Meta:
        abstract = True
        # Any time you inherit from this class, you'll need to indicate which
        # django app it is associated with. For example...
        #   app_label = "third_parties"
