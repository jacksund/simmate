
# Setting up our database

We often want to run the same calculation on many materials, so Simmate pre-builds database tables for us to fill. This just means we make tables (like those used in Excel), where we have all the column headers ready to go. 

For example, you can imagine that a table of structures would have columns for formula, density, and number of sites, among other things. Simmate builds these tables for you and automatically fills all the columns with data after a calculation finishes. 

----------------------------------------------------------------------

## 1. Reset the database

We will explore what these tables look like in tutorial 5, but for now, we want Simmate to create them. All we have to do is run the following command 

``` shell
simmate database reset
```

When you call this command, Simmate will print out a bunch of information -- this can be ignored for now. It's just making all of your tables.

!!! warning
    Every time you run the command `simmate database reset`, your database is deleted and a new one is written with empty tables.  If you want to keep your previous runs, you should save a copy of your database, which can be done by just copy and pasting the database file

----------------------------------------------------------------------

## 2. Finding our database file

So where is the database stored? After running `simmate database reset`, you'll find it in a file named `~/simmate/my_env-database.sqlite3`. 

!!! note
    Notice that your conda envirnment (`my_env` here) is used in the database file name. Simmate does this so you can easily switch between databases just by switching your Anaconda environment. This is useful for testing and developing new workflows, which we will cover in a later tutorial.

To find this file:

1. remember from tutorial 1 that `~` is short for our home directory -- typically something like `/home/jacksund/` or `C:\Users\jacksund`.
2. have "show hidden files" turned on in your File Explorer (on Windows, check "show file name extensions" under the "View" tab). Then you'll see a file named `my_env-database.sqlite3` instead of just `my_env-database`.

You won't be able to double-click this file. Just like how you need Excel to open and read Excel (.xlsx) files, we need a separate program to read database (.sqlite3) files. We'll use Simmate to do this later on.

But just after that one command, our database is setup any ready to use! We can now run workflows and start adding data to it.

----------------------------------------------------------------------
