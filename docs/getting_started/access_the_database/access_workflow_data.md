# Accessing Results from Local Calculations

----------------------------------------------------------------------

## Loading a Table

In the "Run a Workflow" tutorial, we executed a calculation and stored the results in our database table. This section will guide you through accessing these results. 

The results database table is always linked to the workflow via the `database_table` attribute. Here's how to load it:

```python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table
```

----------------------------------------------------------------------

## Viewing Available Columns

To view the data stored in this table, use the `show_columns()` method. This will display all the columns in the table:

```python
table.show_columns()
```

The output will be a list of all the columns in the table. Simmate automatically generates all these columns as they require minimal storage space.

----------------------------------------------------------------------

## Converting to an Excel-like Table

To view the table with all its data, use the `objects` attribute to access the table rows. Then, convert this to a "dataframe" to view the table. A dataframe is a filtered section of a database table. Since we haven't applied any filters to our results, our dataframe will display the entire table. 

```python
data = table.objects.to_dataframe()
```
To view the table, double-click `data` in Spyder's variable explorer (top right window). Here's what a typical dataframe looks like in Spyder:

<!-- This is an image of an Pandas Dataframe in Spyder -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.spyder-ide.org/blog/spyder-variable-explorer/table-headings.png"  height=330 style="max-height: 330px;">
</p>

----------------------------------------------------------------------

## Filtering Results from the Table

You can use the table columns to filter your results. The filtered results will be returned as a list of rows that meet the filtering criteria. In the previous example, we converted this list of results into a dataframe for easier viewing. You can also convert each row into our `ToolkitStructure` from tutorial 3! Feel free to experiment with each:

```python

# You can filter rows in the table using any column!
search_results = table.objects.filter(
    formula_reduced="NaCl",  # check an exact match for any column
    nelements=2,  # filter a column based on a greater or equal to (gte) condition
).all()

# This is just a list of database objects (1 object = 1 row)
print(search_results)

# You can convert this list of objects to a dataframe like we did above
data = search_results.to_dataframe()

# Or you can convert to a list of structure objects (ToolkitStructure)
structures = search_results.to_toolkit()
```

This may not seem very exciting now as we only have one row/structure in our table, but we'll explore more advanced filtering in the next section.

----------------------------------------------------------------------