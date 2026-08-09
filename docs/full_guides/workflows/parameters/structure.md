
The crystal structure to be used for the analysis. The input can be anything compatible with the `Structure` toolkit class. Accepted inputs include:

**a filename (cif or poscar) (recommended)**

=== "yaml"
    ``` yaml
    structure: NaCl.cif
    ```
=== "toml"
    ``` toml
    structure = NaCl.cif
    ```
=== "python"
    ``` python
    structure="NaCl.cif"
    ```

**a dictionary that points to a database entry.** 

=== "yaml"
    ``` yaml
    # example 1
    structure:
        database_table: MatprojStructure
        database_id: mp-123
        
    # example 2
    structure:
        database_table: StaticEnergy
        database_id: 50
    
    # example 3
    structure:
        database_table: Relaxation
        database_id: 50
        structure_field: structure_final
    ```
=== "toml"
    ``` toml
    # example 1
    [structure]
    database_table: MatprojStructure
    database_id: mp-123
        
    # example 2
    [structure]
    database_table: StaticEnergy
    database_id: 50
    
    # example 3
    [structure]
    database_table: Relaxation
    database_id: 50
    structure_field: structure_final
    ```
=== "python"
    ``` python
    # example 1
    structure={
        "database_table": "MatprojStructure",
        "database_id": "mp-123",
    }
    
    # example 2
    structure={
        "database_table": "StaticEnergy",
        "database_id": 50,
    }
    
    # example 3
    structure={
        "database_table": "Relaxation",
        "database_id": 50,
        "structure_field": "structure_final",
    }
    ```

!!! note
    instead of `database_id`, you can also use the `run_id` or `directory` to indicate which entry to load. Further, if the database table is linked to multiple structures (e.g. relaxations have a `structure_start` and `structure_final`), then you can also add the `structure_field` to specify which to choose. 

**a `Structure` object (best for advanced logic)**

=== "python"
    ``` python
    from simmate.toolkit import Structure
    
    structure = Structure(
        lattice=[
            [2.846, 2.846, 0.000],
            [2.846, 0.000, 2.846],
            [0.000, 2.846, 2.846],
        ],
        species=["Na", "Cl"],
        coords=[
            [0.5, 0.5, 0.5],
            [0.0, 0.0, 0.0],
        ],
        coords_are_cartesian=False,
    )
    ```

**a `Structure` database object**

=== "python"
    ``` python
    structure = ExampleTable.objects.get(id=123)
    ```

**json/dictionary serialization from pymatgen**
