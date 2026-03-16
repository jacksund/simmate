
# Viewing data with DBeaver

!!! note
    DBeaver is 100% optional, but without it, you may struggle to understand what your database is & what it even looks like!

----------------------------------------------------------------------

## Why DBeaver?

Just as we use Excel for reading and analyzing `.xlsx` or `.csv` files, DBeaver is our go-to program for working with data from SQL databases. 

This includes managing files like `.sqlite3`, which is the format our Simmate database is currently in. In more advanced cases, we can even use DBeaver to connect to cloud-hosted databases, such as Postgres, which we will cover in a later tutorial.

Ultimately, DBeaver will let us view data as if we were in Excel:

![Table in DBeaver](https://dbeaver.com/wp-content/uploads/2022/03/screen_data_editor.png)

----------------------------------------------------------------------

## Install DBeaver

Download and install [DBeaver Community Edition](https://dbeaver.io/download/). It is free, and you do not need to make an account.

DBeaver is a regular desktop app, so open it once installed. You'll see several components, but they will be empty initially:

![DBeaver interface](https://dbeaver.com/wp-content/uploads/wikidocs_cache/images/ug/appwindow-with-markup.png)

----------------------------------------------------------------------

## Connect to the Simmate Database

1. Select the "New Database Connection" button in the toolbar: ![new db button](https://dbeaver.com/wp-content/uploads/wikidocs_cache/images/ug/new-connection-wizard-button.png)

2. Search for "SQLite", select it, and hit "Next". ![new db button](https://www.sqlite.org/images/sqlite370_banner.gif){ width="50" }

3. Keep the `Connect by:` setting as `Host`. Click `Open ...` and navigate to your database file. It is typically located at `~/simmate/my_env-database.sqlite3` (where `my_env` is your conda environment name).

4. Click `Test Connection ...` (install any requested drivers) and hit `Finish`.

5. Your database will now appear in the `Database Navigator` on the left.


----------------------------------------------------------------------

## Viewing a Table's Data

1. Find your database in `Database Navigator` and `Tables` folder and see everything that Simmate built for you.
2. Scroll down to the `workflows_staticenergy` table and double click to open it in the `Data Editor` (your main panel).
3. You'll see three tabs at the top of the `Data Editor`: `Properties`, `Data`, and `ER Diagram`. Currently, we are looking at the `Properties` tab, which shows us a list of all the columns this table has. To view the actual table and data, select the `Data` tab.
4. If you followed all tutorials, you should see some data from your workflow runs! If you accidentally reset your database, the table will be empty.
5. Take a look at what information was stored from your calculation(s). There are a TON of columns available, so click around / sort by column / fiddle with your data. In the next tutorial, we will learn about why there are so many columns and where they come from.

!!! tip
    If you'd like, you can export the table to a `.csv` file that you can then open in Excel. There is an `Export data` button at the bottom of your `Data` view.

!!! danger
    DBeaver let's you click on & update values within your table. Avoid doing this! You can corrupt and/or misrepresent your data this way. We recommend using DBeaver as if you have read-only permissions to your database.

----------------------------------------------------------------------
