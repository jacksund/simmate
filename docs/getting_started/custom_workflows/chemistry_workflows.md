
# Chemistry Workflows

--------------------------------------------------------------------------------

## A chemistry workflow

The `add` workflow was super basic, so now let's try a more advanced workflow involving a crystal structure.

Here, we will make a workflow that (i) converts a structure to a primitive unitcell and (ii) writes it to a CIF file:

``` python
from simmate.workflows import workflow

@workflow
def write_primitive(structure, directory, **kwargs):
    new_structure = structure.get_primitive_structure()
    new_structure.to(directory / "primitive.cif", fmt="cif")

result = write_primitive.run(structure="POSCAR")
```

!!! note
    Make sure you run this in the same folder that contains the `POSCAR` file from earlier tutorials.

There are several advanced things going in this workflow.

1. We provided `POSCAR` filename (as a python string) -- However, our function is using `structure` as if it was a `toolkit` object (because it calls `get_primitive_structure`). Behind the scenes, Simmate took our `POSCAR` input, decided it was a structure file, and converted it to a `toolkit.Structure` object for us!
2. We didn't provide a `directory` but Simmate built one for us. This is why we can have the code `directory / "primitive.cif"` actually write the file to our new folder.

These advanced feature work let's us run our workflow in new ways. For example, we could run the workflow like so:

``` python
result = write_primitive.run(
    structure={
        "database_table": "MatprojStructure",
        "database_id": "mp-123",
    },
    directory="MyNewFolder",
    compress_output=True,
)
```

This time, we pulled our structure from the database, specified the name of the folder we wanted to make, and that we wanted the final folder converted to a `zip` file once it's done.

So we have lots of new functionality, and all we had to do was add `@workflow` :rocket:

!!! tip
    There are plenty of trick that empower how you run workflows, so be sure to read through our `Parameters` and `Full Guides` section.

--------------------------------------------------------------------------------
