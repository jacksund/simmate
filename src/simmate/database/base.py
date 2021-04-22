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
        In a few cases, you may want to add convience attribute to a model. However,
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

import json

from pymatgen.core.structure import Structure as Structure_PMG

from django.db import models


# --------------------------------------------------------------------------------------


class Structure(models.Model):

    """ Base Info """

    # The structure which is written as a json string from pymatgen's to_json method.
    # To convert back to Structure object, you need to apply json.loads to the string
    # and then Structure.from_dict
    # !!! Postgres does support a dictionary type, but we don't use that here so that
    # !!! we can still test with SQLite3
    # TODO: in the (far) future, I will drop pymatgen dependency
    # TODO: to save on space, I can also come up with a non-json format here
    structure_json = models.TextField()

    # timestamping for when this was added to the database
    created_at = models.DateTimeField(auto_now_add=True)
    # !!! I don't think this column should exist because you shouldn't edit these
    # but I include it
    updated_at = models.DateTimeField(auto_now=True)

    """ Query-helper Info """

    # total number of sites in the unitcell
    nsites = models.IntegerField()

    # number of unique elements
    nelement = models.IntegerField()

    # the base chemical system
    chemical_system = models.CharField(max_length=25)

    # Density of the crystal
    density = models.FloatField()
    
    # TODO: add molar volume
    
    # symmetry info
    # TODO: should this be a relationship to a separate table?
    spacegroup = models.IntegerField()

    # The composition of the structure formatted in various ways
    # OPTIMIZE: which of these are redundant and unnecessary?
    # TODO: add comment for each showing an example.
    formula_full = models.CharField(max_length=50)
    formula_reduced = models.CharField(max_length=25)
    formula_anonymous = models.CharField(max_length=25)

    # TODO: would it make sense to include these extra fields for Lattice/Sites?
    # Lattice: matrix and then... a, b, c, alpha, beta, gamma, volume
    # Sites: abc, xyz, properties, species/element, occupancy

    # For subclasses of this model, it may be useful to add...
    # cell_type (primitive, reduced, supercell, etc.)
    # is_ordered (True/False)
    # charge (float value if charge was added) --> I think this belongs in Calculation

    """ Relationships """
    # For the majority of Structures, you'll want to have a "source" relation that
    # indicates where the structure came from. I don't include this is the abstract
    # model but there are many ways to define it. For example it may relate to another
    # Structure table or even a Calculation. In another case, the entire Structure
    # table may have the same exact source, in which case you'd make a property!

    # Each structure can have many Calculation(s)

    """ Properties """
    """ Model Methods """
    # TODO: If I want a queryset to return a pymatgen Structure object(s) directly,
    # then I need make a new Manager rather than adding methods here. When doing
    # this, also look at my comments in the to_structure method for efficient queries

    @classmethod
    def from_pymatgen(cls, structure, **kwargs):
        # Given a pymatgen structure object, this will return a database structure
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields, which
        # should rarely be done.
        structure_db = cls(
            structure_json=structure.to_json(),
            nsites=structure.num_sites,
            nelement=len(structure.composition),
            chemical_system=structure.composition.chemical_system,
            density=structure.density,
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
        # structure_db = Structure.objects.only("structure_json").get(pk=1)
        # grab the proper Structure entry and we want only the structure column

        # convert the json string to python dictionary
        structure_dict = json.loads(self.structure_json)
        # convert the dictionary to pymatgen Structure object
        structure = Structure_PMG.from_dict(structure_dict)

        return structure

    """ For website compatibility """

    class Meta:
        app_label = "diffusion"  # TODO: move to a separate app
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
        app_label = "diffusion"  # TODO: move to a separate app
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
