
# Viewing the workflow's results

Once your job completes, you may notice a few extra files in your output. One of them is `simmate_summary.yaml`, which contains some quick information for you. Other workflows will also write out plots for you. For example, `electronic-structure` workflows will calculate a band structure using Materials Project settings, and write an image of your final band structure to `band_structure.png`. These extra files and plots vary for each workflow, but they make checking your results nice and quick.

While the plots and summary files are nice for testing, what if we want much more information than what these summary files include -- like density, hull energy, convergence information, etc.? Further, what if we want to adjust our plots or even interact with them? 

To do this we can analyze our final structure and the full results with Simmate's toolkit and database. Accessing these require Python, so our next tutorial will introduce you to Python by directly interacting with the toolkit. We will then work our way up to accessing our database in a follow-up tutorial.

!!! tip
    If you already know python and are comformatable using it, you can view our full guide on how to access database results [here](). Everyone else, we'll work our way up to this :smile:
