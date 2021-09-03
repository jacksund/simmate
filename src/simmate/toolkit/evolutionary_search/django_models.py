# -*- coding: utf-8 -*-

##############################################################################

from django.db import models

##############################################################################


class Composition(models.Model):

    """ Base info """

    # this is the REDUCED formula for the composition (for example 'Ca2N')
    #!!! in the future, maybe I'll change this to specific atom counts
    #!!! but for now, you need to get the num_sites info from the Structure
    formula = models.CharField(max_length=30)

    """ Relationships """
    # has Structure(s) [many]

    """ Inheritance """

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class Structure(models.Model):

    """ Base info """

    # time of initial creation
    #!!! should I move this to ssGen?
    created = models.DateTimeField(auto_now_add=True)

    # time of last update (b/c structure details are overwritten at each ssCalc complete)
    updated = models.DateTimeField(auto_now=True)

    # lattice of the structure
    # I make this a list of [a,b,c,alpha,beta,gamma]
    # I don't want a dict of {'a':1,'b':1,'c':1,...} because that yields a larger entry
    #!!! if I switch to postgres db backend, switch this to a ArrayField made of six FloatFields
    # https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/fields/#arrayfield
    lattice = models.TextField()

    # sites of the structure
    # I make this a list of [coords1,coords2,...] where coords is [x,y,z]
    # I don't want a dict of {'a':1,'b':1,'c':1,...} because that yields a larger entry
    #!!! if I switch to postgres db backend, switch this to a ArrayField made of num_sites ArrayFields, each with 3 FloatFields
    # https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/fields/#arrayfield
    sites = models.TextField()

    # species of the structure
    # I make this a dict of {'Ca':2,'N':1}
    # I don't want a list of ['Ca','Ca','N'] because that yields a larger entry for compositions with >2 sites
    #!!! could I absorb this entry into the Composition model in the future?
    #!!! if I switch to postgres db backend, switch this to a HStoreField
    # https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/fields/#hstorefield
    species = models.TextField()

    """ Relationships """

    #!!! in the future, I could do Lattice and Site models but this may result in larger database
    #!!! this is because there will be the 'relation' columns added to the database
    #!!! alternativately, I could switch from sites to wysites for compressed storage

    # has SingleStructureFingerprint(s) [many]
    # has SingleStructureCalculation(s) [many]

    # the source of the structure
    # I make this ForeignKey because some Generators may output multiple Structures in one run
    source = models.ForeignKey(
        "SingleStructureGeneration",  # this is a string because it's not defined until below
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="outputs",
    )  # naming of structures for ssgen is split between "inputs" and "outputs"

    # this could really be pulled out from the 'sites/species' info but we use a Composition model for convenient querying
    composition = models.ForeignKey(
        Composition, on_delete=models.CASCADE, related_name="structures"
    )

    """ Inheritance """

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################


class BaseClassModel(models.Model):

    """ Base info """

    # the path to the class/module
    # for example: pymatdisc.generators.RandomSymStructure
    name = models.CharField(max_length=50)

    # the settings used to init the class/module
    #!!! if I switch to postgres db backend, switch this to a HStoreField
    # https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/fields/#hstorefield
    settings = models.TextField()

    """ Relationships """

    """ Inheritance """
    # has abstract childs
    class Meta:
        # I don't need a separate table in the database for this
        # Its just a way to quickly give these fields to child classes below
        abstract = True

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################


class Generator(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    """ Relationships """
    # has many Validator(s)
    # has many SingleStructureGeneration(s)

    """ Inheritance """
    # has BaseClassModel abstract parent
    # has PrimaryGenerator child
    # has SecondarGenerator child

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class PrimaryGenerator(Generator):  #!!! Creator

    """ Base info """

    # name from parent
    # settings from parent

    """ Relationships """
    # has many Validator(s)
    # has many SingleStructureGeneration(s)

    """ Inheritance """
    # has Generator parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class SecondaryGenerator(Generator):  #!!! Transformation

    """ Base info """

    # name from parent
    # settings from parent

    """ Relationships """
    # has many Validator(s)
    # has many SingleStructureGeneration(s)

    """ Inheritance """
    # has Generator parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class SingleStructureGeneration(models.Model):

    """ Base info """

    # the settings used to run the Generator
    # for example, I could run Generator.new_structure(spacegroup=166). So I would store {'spacegroup':166}.
    # not all new_structure() methods have required inputs, so I make this input optional
    #!!! if I switch to postgres db backend, switch this to a HStoreField
    # https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/fields/#hstorefield
    settings = models.TextField(
        blank=True, null=True
    )  #!!! make this required and just store empty {} if no settings specified?

    """ Relationships """
    # the Generator applied to create a new structure
    generator = models.ForeignKey(
        Generator,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="ssgenerations",
    )

    # the structures created by running the Generator (other codes call this offspring)
    # has Structure(s) [many] -

    """ Inheritance """
    # has SingleStructurePrimaryGeneration child
    # has SingleStructureSecondaryGeneration child

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class SingleStructurePrimaryGeneration(SingleStructureGeneration):

    """ Base info """

    # settings from parent

    """ Relationships """
    # generator from parent

    # for a ssGen, you access the Structures created via "outputs" tag
    # this distinguishes from other Structures linked to this ssGen that were used as "inputs" (see ssSecGen below)
    # has Structure(s) [many] from parent - output

    """ Inheritance """
    # has SingleStructureGeneration parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class SingleStructureSecondaryGeneration(SingleStructureGeneration):

    """ Base info """

    # settings from parent

    """ Relationships """
    # generator from parent

    # for a ssGen, you access the Structures created via "outputs" tag
    # this distinguishes from other Structures linked to this ssGen that were used as "inputs" (see below)
    # has Structure(s) [many] - outputs

    # the Structure(s) used when running the Generator (other codes call this parents)
    # note the naming of 'inputs' and 'products'
    # input is used because in a ssGen, this Structure is used as a source/input to make a new Structure(s)
    # from the perspective of the input Structure, this ssGen is creating a product/offspring/child of the Structure
    #!!! I make this many because some generators may use multiple structures in one run
    inputs = models.ForeignKey(
        Structure,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="products",
    )  #!!! is there a better name for this? offspring? children? descendents?

    """ Inheritance """
    # has SingleStructureGeneration parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################


class Calculation(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    # the software package used to calculate energy of the structure
    # for example, this could be VASP, CASTEP, QuantumEspresso, ...
    #!!! should I store this here or in the class (that "name" points to)?
    # software = models.CharField(max_length=50)

    """ Relationships """
    # has many SingleStructureCalculation(s)

    """ Inheritance """
    # has BaseClassModel abstract parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class SingleStructureCalculation(models.Model):

    """ Base info """

    # status of the calculation job
    # there are only three options for this
    class StatusOptions(models.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        COMPLETE = "C"
        # ERROR = 'E' #!!! include this for unknown issues?

    status = models.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )

    # the job id for the querying management system (such as slurm)
    job_id = models.CharField(max_length=50)

    # energy output of the calculation
    #!!! consider changing this to fitness for a more generic term
    energy = models.FloatField()

    # special errors / handles / corrections made during the calculation
    #!!! I don't think I can name this 'errors' because of django forms 'errors' attribute
    issues = models.TextField()

    """ Relationships """
    # is one of many outputs from a Calculation type
    calculation = models.ForeignKey(
        Calculation,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="sscalcs",
    )

    # maps to a single Structure, which might have other ssCalcs
    #!!! in the future, should I have many structures -- one for before/after calc or different ionic steps
    structure = models.ForeignKey(
        Structure,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="sscalcs",
    )

    """ Inheritance """

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################

#!!! should I just absorb the Fingerprint model into FingerprintValidator?
class Fingerprint(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    """ Relationships """
    # has many SingleStructureFingerprint(s)

    """ Inheritance """
    # has BaseClassModel abstract parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################


class Validator(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    """ Relationships """

    """ Inheritance """
    # has BaseClassModel abstract parent
    # has BetweenCalcsValidator child
    # has StructureValidator child

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class BetweenCalcsValidator(Validator):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    """ Relationships """
    # calculation done before this validation check
    beforecalc = models.ForeignKey(
        Calculation,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        # related_name='betweencalcsvalidator', #!!! need shorter name
        # blank=True, null=True
    )

    # calculation done after this validation check
    aftercalc = models.ForeignKey(
        Calculation,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        # related_name='betweencalcsvalidator', #!!! need shorter name
        # blank=True, null=True
    )

    """ Inheritance """
    # has Validator parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class StructureValidator(Validator):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel #!!! this would include links to Generators. Do I want to keep track of these?

    """ Relationships """
    generator = models.ForeignKey(
        Generator,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        related_name="validators",  #!!! need shorter name
        # blank=True, null=True
    )

    """ Inheritance """
    # has Validator parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class FingerprintValidator(StructureValidator):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    """ Relationships """
    # the fingerprint method used
    #!!! should I just absorb the Fingerprint model into this?
    method = models.ForeignKey(
        Fingerprint,
        on_delete=models.CASCADE,  #!!! should I cascade or do something else?
        # related_name='betweencalcsvalidator', #!!! need shorter name
        # blank=True, null=True
    )

    """ Inheritance """
    # has StructureValidator parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


#######
# class SingleStructureValidation()
# There are no ssValidations becuase we can assume all existing structures passed
#######

##############################################################################


class Search(models.Model):

    """ Base info """

    """ Relationships """

    # has StructurePool(s) [many]
    # has Trigger(s) [many]
    # has StopCondition(s) [many]

    #!!! for now, I don't actually directly link Structure or Composition objects to a StructurePool or to a Search
    #!!! instead, you would access the structures through all of the Generator(s) linked to this StructurePool
    #!!! I can add easy access via (1) a Manager or (2) model method

    """ Inheritance """

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################

#!!! would population, generation, or something else be better?
class StructurePool(models.Model):

    """ Base info """

    """ Relationships """
    # I limit pools/populations to a single composition for now
    composition = models.ForeignKey(
        Composition, on_delete=models.CASCADE, related_name="pools"
    )  #!!! would struct_pools be better

    # has Generator(s) [many]
    # has Valdiator(s) [many] - specifically BetweenCalcsValidator
    # has Calculation(s) [many] #!!! should this be in Search instead?

    #!!! for now, I don't actually directly link Structure objects to a StructurePool
    #!!! instead, you would access the structures through all of the Generator(s) linked to this StructurePool

    # the overall search that this pool is linked to
    #!!! in the future, I could allow linking this search to other Search (to allow reuse)
    search = models.ForeignKey(
        Search, on_delete=models.CASCADE, related_name="pools"
    )  #!!! would struct_pools be better

    """ Inheritance """

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################

#!!! are Triggers and StopConditions types of Validators?
#!!! alternatively, are Triggers and StopConditions children of a same parent?
# they both do a check and then change the overall search based on that check
# I could also loop in SSCalc to this because of the status..? Might be a stretch though


class Trigger(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    # status of the trigger signal
    # there are only three options for this
    class StatusOptions(models.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        COMPLETE = "C"
        # ERROR = 'E' #!!! include this for unknown issues?

    status = models.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )

    """ Relationships """
    # the search that the trigger is used in
    search = models.ForeignKey(
        Search, on_delete=models.CASCADE, related_name="triggers"
    )

    """ Inheritance """
    # has BaseClassModel abstract parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


class StopCondition(BaseClassModel):

    """ Base info """

    # name from BaseClassModel
    # settings from BaseClassModel

    # status of the stop conditon signal
    # there are only three options for this
    class StatusOptions(models.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        COMPLETE = "C"
        # ERROR = 'E' #!!! include this for unknown issues?

    status = models.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )

    """ Relationships """
    # the search that the stop condition is used in
    search = models.ForeignKey(
        Search, on_delete=models.CASCADE, related_name="stopconditions"
    )

    """ Inheritance """
    # has BaseClassModel abstract parent

    """ Properties """

    """ Model Methods """

    """ Class Methods """


##############################################################################
