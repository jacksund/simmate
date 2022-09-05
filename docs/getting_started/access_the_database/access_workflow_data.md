
# Accessing results from local calculations

## Loading a table

In the "run a workflow" tutorial, we ran a calculation and then added results to our database table. Here, we will now go through the results. 

The database table for results is always attached to the workflow as the `database_table` attribute. You can load it like this:

```python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table
```

## Seeing the available columns

To see all of the data this table stores, we can use it's `show_columns()` method. Here, we'll see a bunch of columns printed for us...

```python
table.show_columns()
```

... which will output ...

```
- id
- created_at
- updated_at
- source
- structure
- nsites
- nelements
- elements
- chemical_system
- density
- density_atomic
- volume
- volume_molar
- formula_full
- formula_reduced
- formula_anonymous
- spacegroup (relation to Spacegroup)
- workflow_name
- location
- directory
- run_id
- corrections
- site_forces
- lattice_stress
- site_force_norm_max
- site_forces_norm
- site_forces_norm_per_atom
- lattice_stress_norm
- lattice_stress_norm_per_atom
- energy
- energy_per_atom
- energy_above_hull
- is_stable
- decomposes_to
- formation_energy
- formation_energy_per_atom
- band_gap
- is_gap_direct
- energy_fermi
- conduction_band_minimum
- valence_band_maximum
```

These are a lot of columns... and you may not need all of them. But Simmate still builds all of these for you right away because they don't take up very much storage space.

## Convert to an excel-like table

Next we'd want to see the table with all of its data. To access the table rows, we use the `objects` attribute, and then to get this into a table, we convert to a "dataframe". A dataframe is a filtered portion of a database table -- and because we didn't filter any of our results yet, our dataframe is just the whole table. 

```python
data = table.objects.to_dataframe()
```
Open up this variable by double-clicking `data` in Spyder's variable explorer (top right window) and you can view the table. Here's what a typical dataframe looks like in Spyder:

<!-- This is an image of an Pandas Dataframe in Spyder -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.spyder-ide.org/blog/spyder-variable-explorer/table-headings.png"  height=330 style="max-height: 330px;">
</p>

## Filtering results from the table

Next, we can use our table columns to start filtering through our results. Your search results will be given back as a list of rows that met the filtering criteria. In the example above, we converted that list of results to into a dataframe for easy viewing. You can also convert each row into our `ToolkitStructure` from tutorial 3! There are a bunch of things to try, so play around with each:

```python

# We can filter off rows in the table. Any column can be used!
search_results = table.objects.filter(
    formula_reduced="NaCl",  # check an exact match for any column
    nelements=2,  # filter a column based on a greater or equal to (gte) condition
).all()

# If we look at this closely, you notice this is just a list of database objects (1 object = 1 row)
print(search_results)

# We can convert this list of objects to a dataframe like we did above
data = search_results.to_dataframe()

# Or we can convert to a list of structure objects (ToolkitStructure)
structures = search_results.to_toolkit()
```

This isn't very exciting now because we just have one row/structure in our table :cry:, but we'll do some more exciting filtering in the next section.
