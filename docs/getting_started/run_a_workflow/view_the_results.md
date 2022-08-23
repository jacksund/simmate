
# Viewing the workflow's results

Once your job completes, you may notice a few extra files in your output. One of them is `simmate_summary.yaml`, which contains some quick information for you.

Simmate can also catch errors, correct them, and retry a calculation. If this occurred during your workflow run, you'll see a file named `simmate_corrections.csv` with all the errors that were incountered and how they were fixed. Note, for our NaCl structure's simple static energy calculation, you likely didn't need any fixes, so this file won't be present.

Other workflows will also write out plots for you. For example, `electronic-structure` workflows will calculate a band structure using Materials Project settings, and write an image of your final band structure to `band_structure.png`. These extra files and plots vary for each workflow, but they make checking your results nice and quick.

While the plots and summary files are nice for testing, what if we want much more information than what these summary files include -- like density, hull energy, convergence information, etc.? Further, what if we want to adjust our plots or even interact with them? 

To do this we can analyze our final structure and the full results with Simmate's toolkit and database. Accessing Simmate's toolkit and database require using python, so our next tutorial will introduce you to python by directly interacting with the toolkit. We will then work our way up to accessing our database in a follow-up tutorial.
