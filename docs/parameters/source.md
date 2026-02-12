
(experimental feature; advanced users only)
This parameter indicates where the input data (and other parameters) came from. The source could be a number of things including a third party id, a structure from a different Simmate database table, a transformation of another structure, a creation method, or a custom submission by the user.

By default, this is a dictionary to account for the many different scenarios. Here are some examples of values used in this column:

=== "python"
    ``` python
    # from a thirdparty database or separate table
    source = {
        "database_table": "MatprojStructure",
        "database_id": "mp-123",
    }
    
    # from a random structure creator
    source = {"creator": "PyXtalStructure"}
    
    # from a templated structure creator (e.g. substituition or prototypes)
    source = {
        "creator": "PrototypeStructure",
        "database_table": "AFLOWPrototypes",
        "id": 123,
    }
    
    # from a transformation
    source = {
        "transformation": "MirrorMutation",
        "database_table":"MatprojStructure",
        "parent_ids": ["mp-12", "mp-34"],
    }
    ```

Typically, the `source` is set automatically, and users do not need to update it.
