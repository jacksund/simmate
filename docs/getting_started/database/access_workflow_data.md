# Accessing Results from Local Calculations

----------------------------------------------------------------------

## Loading a Table

In the "Workflow" tutorial, we executed a calculation and stored the results in our database table. We also learned how to find the table and data in DBeaver. This section will guide you through accessing these results using Python.

The results database table is always linked to the workflow via the `database_table` attribute. Here's how to load it:

```python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.quantum-espresso.quality00")
table = workflow.database_table
```

----------------------------------------------------------------------

## Viewing Available Columns

To view the data stored in this table, use the `show_columns()` method. This will display all the columns in the table:

```python
table.show_columns()
```

The output will be a list of all the columns in the table.

----------------------------------------------------------------------

## Converting to an Excel-like Table

To view a table's data, we will use the `objects` attribute to access the table rows (i.e., 1 object = 1 row). Therefore, something like `table.objects` effectively means "grab all rows of this table". Then to make things easier to view, we will convert these `objects` to a `DataFrame` object, which Spyder let's us open up:

```python
data = table.objects.to_dataframe()
```

To view the table, double-click `data` in Spyder's variable explorer (top right window). Here's what a typical dataframe looks like in Spyder:

<!-- This is an image of an Pandas Dataframe in Spyder -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.spyder-ide.org/blog/spyder-variable-explorer/table-headings.png"  height=330 style="max-height: 330px;">
</p>

----------------------------------------------------------------------

## Basic Filtering

You can also use the table columns to filter your results.

```python
search_results = table.objects.filter(
    formula_reduced="NaCl",
    nelements=2,
).all()
```

In the previous example, we converted this list of results into a dataframe for easier viewing. You can also convert each row into a toolkit `Structure`. Feel free to experiment with each:

``` python
# You can convert this list of objects to a dataframe like we did above
data = search_results.to_dataframe()

# Or you can convert to a list of structure objects (ToolkitStructure)
structures = search_results.to_toolkit()
```

!!! note
    This may not seem very exciting now as we only have one row/structure in our table, but we'll explore more advanced filtering in the next section.

----------------------------------------------------------------------