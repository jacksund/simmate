# Exploring Apps & Data

Simmate is a modular framework. It is designed so that you can add or remove specific features to fit your needs. These groups of features are called **Simmate Apps**.

Think of apps like **plugins** or **extensions** for your favorite web browser. By adding apps, you get access to specialized workflows, databases of crystal structures or molecules, and custom dashboards.

----------------------------------------------------------------------

## 1. Start the Server

Simmate comes with a built-in website that you can run locally to explore these apps. Run this command:

``` bash
simmate run-server
```

Open your web browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/). You will see your local Simmate dashboard.

----------------------------------------------------------------------

## 2. The Materials Project App

Because you chose the prebuilt database in the last step, several popular apps are already installed and loaded with data.

A familiar starting point for most researchers is the **Materials Project** app. This app provides access to the [Materials Project](https://materialsproject.org/) database. Because you downloaded the prebuilt data, you can:

- Search through **over 200,000 crystal structures** from the Materials Project locally on your computer.
- View and manage your data without needing an internet connection.

!!! info
    While the Materials Project app provides ~200,000 structures, Simmate's database as a whole contains even more data from sources like AFLOW, COD, and ChEMBL, all of which are available for local search and analysis.

### Searching the Data

On the left side of your dashboard, find the link to the **Materials Project** and click on it. You can search for structures by:

- **Formula:** Search for "NaCl" or "Fe2O3".
- **Spacegroup:** Search for structures with a specific symmetry (like "Pbnm").
- **ID:** Search for a specific "mp-id" (like "mp-149").

Click on any structure to view its 3D interactive crystal structure, calculated properties, and links to the official Materials Project website.

----------------------------------------------------------------------

## 3. Explore Other Apps

In your local dashboard, click on the **Apps** tab.

This tab lists the apps that provide their own custom user interface and dashboards. Many other apps are also installed "under the hood"—even if they don't have a dedicated page in the Apps tab, they still provide new datasets and workflows that you can find in the **Search** and **Workflows** tabs.

Most popular apps are installed by default, providing a wide range of data and features for your research.
