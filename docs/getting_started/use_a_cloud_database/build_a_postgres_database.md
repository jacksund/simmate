!!! tip
    Ensure you've read the previous section! Database setup can be complex, and most users can bypass it entirely.

-------------------------------------------------------------------------------

## Selecting your database engine

Simmate employs Django ORM for database construction and management, meaning any Django-supported database can be used with Simmate. 

This encompasses PostgreSQL, MariaDB, MySQL, Oracle, SQLite, and others via third-party providers. noSQL databases like MongoDB are supported through [djongo](https://github.com/nesdis/djongo). Comprehensive documentation for Django databases is available [here](https://docs.djangoproject.com/en/4.0/ref/databases/). 

However, **we strongly recommend opting for Postgres**, which we discuss in the following section.

!!! warning
    Our team utilizes SQLite (for local testing) and PostgreSQL (for production), so currently, we can only provide guidance on these two backends. You're free to use others, but be aware that we haven't extensively tested these backends and may not be able to assist with troubleshooting if issues occur.

-------------------------------------------------------------------------------

## Introduction to Postgres setup

PostgreSQL is free and open-source, allowing you to avoid costs and set it up manually.

However, using a database service such as [DigitalOcean](https://www.digitalocean.com/), [Linode](https://www.linode.com/), [GoogleCloud](https://cloud.google.com/), [AWS](https://aws.amazon.com), [Azure](https://azure.microsoft.com/), or another provider is MUCH simpler. These providers set up the database for you through a user-friendly interface.

If you prefer to manually build a Postgres server, numerous tutorials and guides are available ([1](https://www.postgresql.org/docs/current/tutorial.html), [2](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database), etc.). Be aware that this can be time-consuming and your final database connection may be slower if your team operates from multiple locations. 

-------------------------------------------------------------------------------

## Setting up Postgres with DigitalOcean

### Introduction & expected costs

Our team uses DigitalOcean, where the basic database server (~$15/month) is sufficient for Simmate usage. You'll only need >10GB if you're running >100,000 structure relaxations or frequently using unit cells with >1000 atoms.

### (i) Account creation

Start by creating an account on DigitalOcean using [this link](https://m.do.co/c/8aeef2ea807c) (our referral). We suggest signing in with your Github account. This referral link provides:

1. $100 credit for servers from DigitalOcean (valid for 60 days)
2. $10 credit for the Simmate team from DigitalOcean, helping fund our servers

If you encounter any issues, please verify that DigitalOcean is still offering this deal [here](https://try.digitalocean.com/freetrialoffer/). Simmate is not affiliated with DigitalOcean.

### (ii) Cloud database creation

1. On the DigitalOcean dashboard, click the green "Create" button in the top right and select "Database". This should take you to [this page](https://cloud.digitalocean.com/databases/new).
2. For "database engine", select the latest version of PostgreSQL (currently v14)
3. Leave the rest of the page's options at their default values.
4. Click **Create a Database Cluster** when ready.
5. On your new cluster's homepage, there's a "Get Started" button. We'll go through this dialog in the next section.

Note, this is the database **cluster**, which can host multiple databases (each with their own tables).

### (iii) Database connection

Before setting up our database on this cluster, we'll first try connecting to the default database on it (named `defaultdb`).

1. On your new database's page, you'll see a "Getting Started" dialog -- select it!
2. "Restrict inbound connections" is optional and beginners should skip it for now. We skip this because if you're running calculations on a supercomputer/cluster, you'll need to add **ALL** the associated IP addresses for connections to work properly. That's a lot of IP addresses to collect and configure correctly -- so we leave this to advanced users.
3. "Connection details" is the information we need to provide to Simmate/Django. Let's copy this information. For example, here's what the details look like on DigitalOcean:
```
username = doadmin
password = asd87a9sd867fasd
host = db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
port = 25060
database = defaultdb
sslmode = require
```
5. In your Simmate Python environment, ensure you have the Postgres engine installed. The package is `psycopg2`, which allows Django to communicate with Postgres. To install this, run the command:
``` bash
conda install -n my_env -c conda-forge psycopg2
```

4. We need to pass this information to Simmate (which connects using Django). To do this, add a file named `my_env-database.yaml` (using your conda env name) to your Simmate config directory (`~/simmate`) with the following content -- make sure to substitute in your connection information and note that ENGINE tells Django we are using Postgres:
``` yaml
default:
  ENGINE: django.db.backends.postgresql
  HOST: db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: defaultdb
  USER: doadmin
  PASSWORD: asd87a9sd867fasd
  PORT: 25060
  OPTIONS:
    sslmode: require
```
5. Verify that you can connect to this database on your local computer by running the following in Spyder:
``` python
from simmate.configuration import settings

print(settings.database)  # this should display your connect info!
```

### (iv) Creating a separate database for testing (on the same server)

Just as we don't use the `(base)` environment in Anaconda, we don't want to use the default database `defaultdb` on our cluster. Here we'll create a new database -- one that we can delete if we want to start over.

1. On DigitalOcean with your Database Cluster page, select the "Users&Databases" tab.
2. Create a new database using the "Add new database" button and name it `simmate-database-00`. We name it this way because you may want to create new/separate databases and numbering is a quick way to keep track of these.
3. In your connection settings (from the section above), switch the NAME from defaultdb to `simmate-database-00`. You will change this in your `my_env-database.yaml` file.

### (v) Building our database tables

Now that we've set up and connected to our database, we can create our Simmate database tables and start populating them with data! We do this the same way we did without a cloud database:

1. In your terminal, ensure you have your Simmate environment activated
2. Run the following command: 
``` bash
simmate database reset
```
3. You're now ready to start using Simmate with your new database!

### (vi) Creating a connection pool

When we have multiple calculations running simultaneously, we need to ensure our database can handle all these connections. Therefore, we create a connection pool which allows for thousands of connections. This "pool" operates like a waitlist where the database handles each connection request in sequence.

1. Select the "Connection Pools" tab and then "Create a Connection Pool"
2. Name your pool `simmate-database-00-pool` and select `simmate-database-00` for the database
3. Select "Transaction" for our mode (the default) and set our pool size to **10** (or adjust this value as needed)
4. Create the pool when ready!
5. You'll need to update your `my_env-database.yaml` file to these connection settings. At this point your file will look similar to this (note, our NAME and PORT values have changed):
``` yaml
default:
  ENGINE: django.db.backends.postgresql
  HOST: db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool  # THIS LINE WAS UPDATED
  USER: doadmin
  PASSWORD: asd87a9sd867fasd
  PORT: 25061
  OPTIONS:
    sslmode: require
```

!!! warning
    Calling `simmate database reset` when using a connection pool will NOT work!
    If you ever need to reset your database, ensure you connect to the database
    directly instead of through a database pool.

### (vii) Loading third-party data

This step is optional.

With Sqlite, we could download a prebuilt database with data from third parties already in it. However, creating our Postgres database means our database is entirely empty.

To load **ALL** third-party data (~5GB total), you can use the following command. We can also use Dask to run this in parallel and speed things up. Depending on your internet connection and CPU speed, this can take up to 24 hours.

``` shell
simmate database load-remote-archives --parallel
```

!!! warning
    `--parallel` will use all cores on your CPU. Keep this in mind if you are
    running other programs/calculations on your computer already.

### (viii) Sharing the database

If you want to share this database with others, they simply need to copy your config file: `my_env-database.yaml`. They won't need to run `simmate database reset` because you did it for them.

-------------------------------------------------------------------------------