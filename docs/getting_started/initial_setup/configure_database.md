# Database Configuration

----------------------------------------------------------------------

## What is the database?

The Simmate database is just a list of tables -- so you can imagine an Excel spreadsheet where there are a bunch of pre-set tables and column headers. Simmate then fills the table with data whenever we run workflows or download datasets.

!!! example
    Let's say we want a table for crystal structures. It would have columns for formula, density, and number of sites, among other things. Likewise, a static-energy calculation would have columns for final energy, CPU time, and more. Rather than build & fill these tables from scratch, we let Simmate handle all of this.

!!! note
    Our deep-dive database tutorial will come after we learn about workflows. For now, just know we are setting up the database so that we have somewhere to store results and access existing data.

----------------------------------------------------------------------

## 1. Database Initialization

To create the database, run the following command in your terminal:

``` shell
simmate database reset
```

During this process, Simmate will ask if you want to use the **prebuilt database**. 

**You should answer "yes" to this prompt.**

```text
It looks like you are using the default database backend (sqlite3). 
Would you like to use a prebuilt-database with all third-party data already loaded? 
If this is the first time you using the prebuild, this will involve a ~1.5GB 
download and will unpack to roughly 10GB.

We recommend answering 'yes' for beginners.
```

By answering yes, Simmate downloads a pre-packaged database file that includes datasets from the **Materials Project**, **ChEMBL**, **COD**, and others. This saves you the time and effort of downloading and loading these datasets individually.

!!! warning
    Be aware that running the command `simmate database reset` will delete your existing database and replace it with a new one. If you have run calculations previously and want to keep your data, make sure to backup your database before running this command.

----------------------------------------------------------------------

## 2. Locating the Database File

After the command finishes, your database is located in a file named `~/simmate/my_env-database.sqlite3`.

To find this file, remember that `~` is shorthand for your home directory, which is typically something like `/home/johnsmith/` or `C:\Users\johnsmith`.

By default, Simmate stores all its configuration, settings, and local database files in this directory.

This file can't be opened by simply double-clicking. Just as Excel is needed to open and read Excel (`.xlsx`) files, a separate program is required to read database (`.sqlite3`) files. Simmate provides a built-in web dashboard to read and interact with this file easily, which we will explore next.

!!! note
    Notice that the name of your virtual environment (`my_env` in this case) is part of the database file name. This is a Simmate feature that lets you switch between databases by simply changing your environment. This is especially handy when testing and developing new workflows.

----------------------------------------------------------------------
