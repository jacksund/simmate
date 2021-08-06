# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------


"""

Every base model class has the sections shown below. These are simply to organize the
code and make it easier to read:

    Base Info
        These fields are the absolute minimum required for the object and can be
        considered the object's raw data.

    Query-helper Info
        These fields aren't required but exist simply to help with common query
        functions. For example, a structure's volume can be calculated using the
        base info fields, but it helps to have this data in a separate column to
        improve common query efficiencies at the cost of a larger database.

    Relationships
        These fields point to other models that contain related data. For example,
        a single structure may be linked to calculations in several other tables.
        The relationship between a structure and it's calculations can be described
        in this section. Note that the code establishing the relationship only exists
        in one of the models -- so we simply add a comment in the other's section.
        TYPES OF RELATIONSHIPS:
            ManyToMany - place field in either but not both
            ManyToOne (ForeignKey) - place field in the many
            OneToOne - place field in the one that has extra features

    Properties
        In a few cases, you may want to add a convience attribute to a model. However,
        in the majority of cases, you'll want to convert the model to some other
        class first which has all of the properties you need. We separate classes
        in this way for performance and clarity. This also allows our core and
        database to be separate and thus modular.

    Model Methods
        These are convience functions added onto the model. For example, it's useful
        to have a method to quickly convert a model Structure (so an object representing
        a row in a database) to a pymatgen Structure (a really powerful python object)

    For website compatibility
        This contains the extra metadata and code needed to get the class to work
        with Django and other models properly.

"""

from scipy.constants import Avogadro
from pymatgen.core.structure import Structure as Structure_PMG

from django.db import models


# --------------------------------------------------------------------------------------


class Structure(models.Model):

    """ Base Info """
    
    # The id used to symbolize the structure.
    # For example, Materials Project structures are represented by ids such as
    # "mp-12345" while AFLOW structures by "aflow-12345"
    id = models.CharField(max_length=25, primary_key=True)

    # The structure which is written to a string and in a compressed format 
    # using the .from_pymatgen() method. To get back to our pymatgen structure
    # object, use the .to_pymatgen() method!
    structure_str = models.TextField()

    # !!! Should I have timestamps for the third-party databases?
    # timestamping for when this was added to the database
    # created_at = models.DateTimeField(auto_now_add=True)
    # !!! I don't think this column should exist because you shouldn't edit these
    # but I include it anyways
    # updated_at = models.DateTimeField(auto_now=True)

    """ Query-helper Info """

    # total number of sites in the unitcell
    nsites = models.IntegerField()

    # total number of unique elements
    nelement = models.IntegerField()

    # the base chemical system (ex: "Y-C-F")
    chemical_system = models.CharField(max_length=25)

    # Density of the crystal (g/L)
    density = models.DecimalField(max_digits=7, decimal_places=3)

    # Molar volume of the crystal (mL/mol)
    # Note we prefer this over a "volume" field because volume is highly dependent
    # on the symmetry and the arbitray unitcell. If you are truly after small volumes
    # of the unitcell, it is likely you really just want to search by spacegroup.
    molar_volume = models.DecimalField(max_digits=7, decimal_places=3)

    # symmetry info
    # TODO: should this be a relationship to a separate table?
    spacegroup = models.IntegerField()

    # The composition of the structure formatted in various ways
    # BUG: The max length here is overkill because there are many structures
    # with 8+ elements and disordered formula (e.g. "Ca2.103 N0.98")
    formula_full = models.CharField(max_length=50)  # more
    formula_reduced = models.CharField(max_length=50)
    formula_anonymous = models.CharField(max_length=50)

    # TODO: would it make sense to include these extra fields for Lattice/Sites?
    # Lattice: matrix and then... a, b, c, alpha, beta, gamma, volume
    # Sites: abc, xyz, properties, species/element, occupancy
    # Personally, I'm against it because users shouldn't be querying by these.

    # For subclasses of this model, it may be useful to add...
    # cell_type (primitive, reduced, supercell, etc.)
    # is_ordered (True/False) --> for many databases this is always True
    # charge (float value if charge was added) --> I think this belongs in Calculation

    """ Relationships """
    # For the majority of Structures, you'll want to have a "source" relation that
    # indicates where the structure came from. I don't include this is the abstract
    # model but there are many ways to define it. For example it may relate to another
    # Structure table or even a Calculation. In another case, the entire Structure
    # table may have the same exact source, in which case you'd make a property!

    # Each structure can have many Calculation(s)

    """ Properties """
    # none

    """ Model Methods """
    # TODO: If I want a queryset to return a pymatgen Structure object(s) directly,
    # then I need make a new Manager rather than adding methods here. When doing
    # this, also look at my comments in the to_structure method for efficient queries

    @classmethod
    def from_pymatgen(cls, structure, **kwargs):

        # OPTIMIZE: I currently store files as poscar strings for ordered structures
        # and as CIFs for disordered structures. Both of this include excess information
        # that slightly inflates file size, so I will be making a new string format in
        # the future. This will largely be based off the POSCAR format, but will
        # account for disordered structures and all limit repeated data (such as the
        # header line, "direct", listing each element/composition, etc.).
        storage_format = "POSCAR" if structure.is_ordered else "CIF"

        # Given a pymatgen structure object, this will return a database structure
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields.
        structure_db = cls(
            # OPTIMIZE: The structure_json is not the most compact format. Others
            # like POSCAR are more compact and can save space. This is at the cost of
            # being robust to things like fractional occupancies. Perhaps a new compact
            # format needs to be made specifically for Simmate.
            structure_str=structure.to(fmt=storage_format),
            nsites=structure.num_sites,
            nelement=len(structure.composition),
            chemical_system=structure.composition.chemical_system,
            density=structure.density,
            # 1e-27 is to convert from cubic angstroms to Liter and then 1e3 to
            # mL. Therefore this value is in mL/mol
            # OPTIMIZE: move this to a class method
            molar_volume=(structure.volume / structure.num_sites)
            * Avogadro
            * 1e-27
            * 1e3,
            spacegroup=structure.get_space_group_info(0.1)[1],  # OPTIMIZE
            formula_full=structure.composition.formula,
            formula_reduced=structure.composition.reduced_formula,
            formula_anonymous=structure.composition.anonymized_formula,
            **kwargs,  # this allows subclasses to add fields with ease
        )
        return structure_db

    def to_pymatgen(self):
        # Converts the database object to pymatgen structure object

        # NOTE: if you know this is what you're going to do from a query, then
        # it is more efficient to only grab the structure_json column because
        # that's all you need! You'd do that like this:
        #   structure_db = Structure.objects.only("structure_json").get(id="example-id")
        # This grabs the proper Structure entry and only the structure column.

        # convert the stored string to python dictionary.
        # OPTIMIZE: see my comment on storing strings in the from_pymatgen method above.
        # For now, I need to figure out if I used "CIF" or "POSCAR" and read the structure
        # accordingly. In the future, I can just assume my new format.
        # If the string starts with "#", then I know that I stored it as a "CIF".
        storage_format = "CIF" if (self.structure_json[0] == "#") else "POSCAR"

        # convert the string to pymatgen Structure object
        structure = Structure_PMG.from_str(
            self.structure_json,
            fmt=storage_format,
        )

        return structure

    """ For website compatibility """

    class Meta:
        app_label = "third_parties"  # TODO: move to a separate app
        abstract = True


# --------------------------------------------------------------------------------------


class Calculation(models.Model):

    """ Base info """

    # Indicate what state the calculation is in. This exists to ensure we don't
    # submit multiple to Prefect and also let's us check how many currently exist in
    # the queue.
    # !!! If you choose to change these, consider Prefect's different state labels:
    #       https://docs.prefect.io/api/latest/engine/state.html
    class StatusTypeOptions(models.TextChoices):
        SCHEDULED = "S"
        COMPLETED = "C"
        FAILED = "F"

    status = models.CharField(
        max_length=1,
        choices=StatusTypeOptions.choices,
        default=StatusTypeOptions.SCHEDULED,
    )

    # timestamping for when this was added to the database
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    """ Relationships """
    # While there are no base relations for this abstract class, the majority of
    # calculations will link to a structure or alternatively a diffusion pathway
    # or crystal surface. In such cases, you'll add a relationship like this:
    # structure = models.OneToOneField(
    #     Structure,
    #     primary_key=True,
    #     on_delete=models.CASCADE,
    # )

    """ Properties """
    """ Model Methods """
    # none implemented yet

    """ Restrictions """
    # none

    """ For website compatibility """
    """ Set as Abstract Model """
    # I have other model inherit from this one, while this model doesn't need its own
    # table. Therefore, I set this as an abstract model. Should that change in the
    # future, look here:
    # https://docs.djangoproject.com/en/3.1/topics/db/models/#model-inheritance
    class Meta:
        app_label = "third_parties"  # TODO: move to a separate app
        abstract = True


# --------------------------------------------------------------------------------------

"""
TODO: these are ideas for other models that I still need to write. Some are based
off of the Materials Project MapiDoc and will likely change a lot.

StructureCluster (or MatchingStructures)
    This is maps to a given structure in primary structure table and links that
    structures relations to all other databases. For example, it will map to the
    list of mp-ids and icsd-ids that match the structure within a given tolerance.
    This subclasses Calculation because structure matching takes a really long time
    and even needs to be reran on occasion.
    ICSD, MP, AFLOW, JARVIS, etc...

EnergyCalculation
    final_energy
    e_above_hull
    final_energy_per_atom
    formation_energy_per_atom

    # for relaxation
    delta_volume(%)

    # settings (may be properties!)
    encut
    nkpts --> kpt density
    psudeopotential
        functional(PBE)
        label(Y_sv)
        pot_type(PAW)
    run_type(GGA,GGAU,HF)
    is_hubbard

Spacegroup
    number
    crystal_system
    hall
    number
    pointgroup
    source
    symbol

BandStructure + DOS
    band_gap
    is_direct
    type
    efermi

Dielectric
    e_electronic
    e_total
    n
    poly_electronic
    poly_total

Elasticity + ElesticityThirdOrder
    (G=shear; K=bulk)
    G_Reuss
    G_VRH
    G_Voigt
    G_Voight_Reuss_Hill
    K_Reuss
    K_VRH
    K_Voight
    K_Voight_Reuss_Hill
    compliance_tensor
    elastic_anisotropy
    elastic_tensor
    elastic_tensor_original
    homogeneous_poisson	nsites
    poisson_ratio
    universal_anisotropy
    warnings
    **lots for elasticity_third_order so I haven't added these yet

Magnetism
    exchange_symmetry
    is_magnetic	magmoms	num_magnetic_sites
    num_unique_magnetic_sites
    ordering
    total
    total_magnetization
    total_magnetization_normalized_formula_units
    total_magnetization_normalized_vol
    types_of_magnetic_species

Oxides
    type (peroxide/superoxide/etc)

Piezo
    eij_max
    v_max
    piezoelectric_tensor

"""

# --------------------------------------------------------------------------------------
