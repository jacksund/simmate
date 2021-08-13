# -*- coding: utf-8 -*-

from scipy.constants import Avogadro

from django.db import models

from pymatgen.core.structure import Structure as Structure_PMG

# from pymatgen.analysis.prototypes import AflowPrototypeMatcher

from simmate.database.symmetry import Spacegroup


class Structure(models.Model):

    """Base Info"""

    # The id used to symbolize the structure.
    # For example, Materials Project structures are represented by ids such as
    # "mp-12345" while AFLOW structures by "aflow-12345"
    id = models.CharField(max_length=25, primary_key=True)

    # The structure which is written to a string and in a compressed format
    # using the .from_pymatgen() method. To get back to our pymatgen structure
    # object, use the .to_pymatgen() method!
    structure_string = models.TextField()

    """ Query-helper Info """

    # total number of sites in the unitcell
    nsites = models.IntegerField()

    # total number of unique elements
    nelements = models.IntegerField()

    # the base chemical system (ex: "Y-C-F")
    chemical_system = models.CharField(max_length=25)

    # Density of the crystal (g/cm^3)
    density = models.FloatField()

    # Molar volume of the crystal (cm^3/mol)
    # Note we prefer this over a "volume" field because volume is highly dependent
    # on the symmetry and the arbitray unitcell. If you are truly after small volumes
    # of the unitcell, it is likely you really just want to search by spacegroup.
    molar_volume = models.FloatField()

    # The composition of the structure formatted in various ways
    # BUG: The max length here is overkill because there are many structures
    # with 8+ elements and disordered formula (e.g. "Ca2.103 N0.98")
    formula_full = models.CharField(max_length=50)  # more
    formula_reduced = models.CharField(max_length=50)
    formula_anonymous = models.CharField(max_length=50)

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
    # TODO: this will be a relationship in the future
    spacegroup = models.ForeignKey(Spacegroup, on_delete=models.PROTECT)

    # The AFLOW prototype that this structure maps to.
    # TODO: this will be a relationship in the future
    # prototype = models.CharField(max_length=50, blank=True, null=True)

    """ Properties """
    # none

    """ Model Methods """

    @classmethod
    def from_pymatgen(cls, structure, **kwargs):

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
        structure_db = cls(
            # OPTIMIZE: The structure_json is not the most compact format. Others
            # like POSCAR are more compact and can save space. This is at the cost of
            # being robust to things like fractional occupancies. Perhaps a new compact
            # format needs to be made specifically for Simmate.
            structure_string=structure.to(fmt=storage_format),
            nsites=structure.num_sites,
            nelements=len(structure.composition),
            chemical_system=structure.composition.chemical_system,
            density=structure.density,
            # 1e-27 is to convert from cubic angstroms to Liter and then 1e3 to
            # mL. Therefore this value is in mL/mol
            # OPTIMIZE: move this to a class method
            molar_volume=(structure.volume / structure.num_sites)
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
        return structure_db

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
