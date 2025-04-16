# Database Configuration

----------------------------------------------------------------------

## What is the database?

The Simmate database is just a list of tables -- so you can imagine an Excel spreadsheet where there are a bunch of pre-set tables and column headers. Simmate then fills the table with data whenever we run workflows. 

!!! example
    Let's say we want a table for crystal structures. It would have columns for formula, density, and number of sites, among other things. Likewise, a static-energy calculation would have columns for final energy, CPU time, and more. Rather than build & fill these tables from scratch, we let Simmate handle all of this.

!!! note
    Our database tutorial will come after we learn about workflows. For now, just know we building the database so that we have somewhere to store results.

----------------------------------------------------------------------

## 1. Database Initialization

To create the database, run the following command. Say yes to each prompt too:

``` shell
simmate database reset
```

And that's it! With just one command, our database is ready for use. We can now run workflows and start filling it with data. :rocket:

!!! warning
    Be aware that running the command `simmate database reset` will delete your existing database and replace it with an empty one. To keep your previous data, make sure to backup your database by copying and pasting the database file.

----------------------------------------------------------------------

## 2. Locating the Database File

After running `simmate database reset`, the database can be located in a file named `~/simmate/my_env-database.sqlite3`.

To find this file, remember that `~` is shorthand for our home directory, which is typically something like `/home/johnsmith/` or `C:\Users\johnsmith`.

This file can't be opened by double-clicking. Just as Excel is needed to open and read Excel (`.xlsx`) files, a separate program is required to read database (`.sqlite3`) files. We'll use Simmate (& DBeaver) for this later.

!!! note
    Note that the name of your conda environment (`my_env` in this case) is part of the database file name. This is a Simmate feature that lets you switch between databases by simply changing your Anaconda environment. This is especially handy when testing and developing new workflows, which we'll discuss in a future tutorial.

----------------------------------------------------------------------
