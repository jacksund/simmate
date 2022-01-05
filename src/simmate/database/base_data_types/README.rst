
Every base model class has the sections shown below. These are simply to organize the
code and make it easier to read:

Base Info:
    These fields are the absolute minimum required for the object and can be
    considered the object's raw data.

Query-helper Info:
    These fields aren't required but exist simply to help with common query
    functions. For example, a structure's volume can be calculated using the
    base info fields, but it helps to have this data in a separate column to
    improve common query efficiencies at the cost of a larger database.

Relationships:
    These fields point to other models that contain related data. For example,
    a single structure may be linked to calculations in several other tables.
    The relationship between a structure and it's calculations can be described
    in this section. Note that the code establishing the relationship only exists
    in one of the models -- so we simply add a comment in the other's section.
    TYPES OF RELATIONSHIPS:
        ManyToMany - place field in either but not both
        ManyToOne (ForeignKey) - place field in the many
        OneToOne - place field in the one that has extra features

Properties:
    In a few cases, you may want to add a convience attribute to a model. However,
    in the majority of cases, you'll want to convert the model to some other
    class first which has all of the properties you need. We separate classes
    in this way for performance and clarity. This also allows our core and
    database to be separate and thus modular.

Model Methods:
    These are convience functions added onto the model. For example, it's useful
    to have a method to quickly convert a model Structure (so an object representing
    a row in a database) to a pymatgen Structure (a really powerful python object)

For website compatibility:
    This contains the extra metadata and code needed to get the class to work
    with Django and other models properly.
