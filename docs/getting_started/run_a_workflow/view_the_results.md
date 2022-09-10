
# Viewing the workflow's results


## Basic output files

Once your job completes, you may notice a few extra files in your output. One of them is `simmate_summary.yaml`, which contains some quick information for you.

The information in this file is a snippet of what's available in the database:
``` yaml
_DATABASE_TABLE_:
...
```

Other workflows will also write out plots for you. For example, `electronic-structure` workflows will calculate a band structure using Materials Project settings, and write an image of your final band structure to `band_structure.png`. These extra files and plots vary for each workflow, but they make checking your results nice and quick.

----------------------------------------------------------------------

## The website view

In the `simmate_summary.yaml` file, there is the `_WEBSITE_URL_`. You can copy/paste this URL into your browser and view your results in an interactive format. Just make sure you are running your local server first:

``` shell
simmate run-server
```

!!! note
    Remember that the server and your database are limited to your local computer. Trying to access a URL on a computer that doesn't share the same database file will not work -- so you may need to copy your database file from the cluster to your local computer. Or even better -- if you would like to access results through the internet, then you have to switch to a cloud database (which is covered in a later tutorial).

----------------------------------------------------------------------

## Advanced data analysis

We can analyze our final structure and the full results with Simmate's toolkit and database. Accessing these require Python, so our next tutorial will introduce you to Python by directly interacting with the toolkit. We will then work our way up to accessing our database in a follow-up tutorial.

----------------------------------------------------------------------

