# Submitting a Workflow

In the last section, you explored the data and apps available in Simmate. Now let's look at how to run a **workflow** using the web dashboard.

----------------------------------------------------------------------

## 1. What is a Workflow?

A workflow is an automated task that runs a calculation. For example, a workflow might take a crystal structure, run a simulation (like VASP or Quantum Espresso) to relax it to its lowest energy state, and then save the final energy to your database.

Many apps come with their own standardized workflows. By using these built-in workflows, you are using expert settings that have been tested and verified, ensuring your calculations are accurate and comparable to large databases like the Materials Project.

----------------------------------------------------------------------

## 2. Navigate to Workflows

If your server isn't running, start it up:
```bash
simmate run-server
```

Open your dashboard at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). 

In the navigation menu on the left, click on the **Workflows** tab. Here you will see a list of all the workflows available to you. You can browse through them or use the search bar to find a specific one (e.g., search for "relaxation").

----------------------------------------------------------------------

## 3. Submit a Workflow

Click on any workflow to view its details. You'll see an explanation of what the workflow does and a form to submit a new run.

1. **Find the Submission Form:** On the workflow details page, look for the "Submit a Run" section.
2. **Fill out the Parameters:** Depending on the workflow, you might need to provide an input structure (like uploading a `.cif` file) or specify a few parameters.
3. **Submit:** Click the "Run Workflow" or "Submit" button.

!!! tip
    If you do not have an input structure to submit, that is fine! We will cover how to build a input structure in the next section. This tutorial is just to let you know where things are in the website. 

### What happens next?

Once you click submit, Simmate adds your request to a "queue" in your database. 

If you look at your list of workflow runs now, you'll see your newly submitted task in a **"Pending"** state. This is because Simmate hasn't actually started the calculation yet! 

To actually run the simulation software (like VASP, QE, or RDKit), you need to set up a **"Worker"**. Think of a Worker as a background process that watches the queue and does the actual work. We will show you how to set up your first Worker in a later tutorial. For now, just know that your workflow is safely stored and ready to be processed.

----------------------------------------------------------------------

## Next Steps

Now that you are familiar with the Simmate ecosystem and dashboard, it's time to dive deeper. In the next section, we'll learn how to submit and manage workflows programmatically using the **Command-Line (CLI)** and **Python**. This is essential for scaling your research and automating complex tasks!
