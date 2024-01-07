# Database Configuration

Simmate enables multi-material calculations by pre-building database tables. These tables, akin to Excel spreadsheets, have pre-set column headers. 

Take for example a table of structures, which may have columns for formula, density, and number of sites, among others. Simmate not only generates these tables but also fills the columns with data once a calculation is completed. 

----------------------------------------------------------------------

## 1. Database Initialization

We'll explore the structure of these tables in tutorial 5. For now, we need Simmate to create them. This can be done by running the following command:

``` shell
simmate database reset
```

Upon execution, Simmate will show a series of messages. These can be ignored at this point as they relate to the table creation process.

!!! warning
    Be aware that running the command `simmate database reset` will delete your existing database and replace it with a new one with empty tables. To keep your previous runs, make sure to backup your database by copying and pasting the database file.

----------------------------------------------------------------------

## 2. Locating the Database File

After running `simmate database reset`, the database can be located in a file named `~/simmate/my_env-database.sqlite3`. 

!!! note
    Note that the name of your conda environment (`my_env` in this case) is part of the database file name. This is a Simmate feature that lets you switch between databases by simply changing your Anaconda environment. This is especially handy when testing and developing new workflows, which we'll discuss in a future tutorial.

To find this file, remember from tutorial 1 that `~` is a shorthand for our home directory, typically something like `/home/jacksund/` or `C:\Users\jacksund`.

This file can't be opened by double-clicking. Just as Excel is needed to open and read Excel (.xlsx) files, a separate program is required to read database (.sqlite3) files. We'll use Simmate for this later.

With just one command, our database is ready for use! We can now run workflows and start filling it with data.

----------------------------------------------------------------------