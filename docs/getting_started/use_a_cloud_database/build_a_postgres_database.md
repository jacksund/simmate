
!!! tip
    Make sure you have read the previous section! Setting up a database can be tricky, and the majority of users can avoid it altogether.

-------------------------------------------------------------------------------

## Choosing your database engine

Simmate uses Django ORM to build and manage its database, so any Django-supported database can be used with Simmate. 

This includes PostgreSQL, MariaDB, MySQL, Oracle, SQLite, and others through third-parties. noSQL databases like MongoDB are supported through [djongo](https://github.com/nesdis/djongo). The full documentation for django databases is available [here](https://docs.djangoproject.com/en/4.0/ref/databases/). 

However, **we strongly recommended choosing Postgres**, which we cover in the next
section.

!!! warning
    Our team uses SQLite (for local testing) and PostgreSQL (for production), so at the moment, we can only offer guidance on these two backends. You are welcome to use the others, but be wary that we haven't thuroughly tested these backends and won't be able to help you troubleshoot if errors arise.

-------------------------------------------------------------------------------

## Intro to Postgres set up

PostgreSQL is free and open-source, so you can avoid costs and set it up manually.

However, it's MUCH easier to use a database service such as [DigitalOcean](https://www.digitalocean.com/), [Linode](https://www.linode.com/), [GoogleCloud](https://cloud.google.com/), [AWS](https://aws.amazon.com), [Azure](https://azure.microsoft.com/), or another provider. These providers set up the database for you through a nice user-interface.

If you still want to manually build a postgres server, there are many tutorials and guides available on how to do this ([1](https://www.postgresql.org/docs/current/tutorial.html), [2](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database), etc.). Just be aware that this is can take a lot of time AND your final database connection may be slower if your team works accross multiple locations. 

-------------------------------------------------------------------------------

## Setup Postgres with DigitalOcean

### Intro & expected costs

Our team uses DigitialOcean, where the starter database server (~$15/month) is plenty for Simmate usage. You'll only need >10GB if you are running >100,000 structure relaxations or frequently using unitcells with >1000 atoms.


### (i) create an account

To start, make an account on DigitalOcean using [this link](https://m.do.co/c/8aeef2ea807c) (which uses our refferal). We recommend using your Github account to sign in. This referral link does two things:

1. DigitialOcean gives you $100 credit for servers (for 60 days)
2. DigitialOcean gives the Simmate team $10 credit, which will help fund our servers

If you have any issues, please make sure that DigitalOcean is still actually offering this deal [here](https://try.digitalocean.com/freetrialoffer/). Simmate is not affiliated with DigitalOcean.


### (ii) create the cloud database

1. On our DigitalOcean dashboard, click the green "Create" button in the top right and then select "Database". It should bring you to [this page](https://cloud.digitalocean.com/databases/new).
2. For "database engine", select the newest version of PostgreSQL (currently v14)
3. The remainder of the page's options can be left at their default values.
4. Select **Create a Database Cluster** when you're ready.
5. For the new homepage on your cluster, there is a "Get Started" button. We will go through this dialog in the next section.

Note, this is the database **cluster**, which can host multiple databases on it (each with all their own tables).


### (iii) connect to the database

Before we set up our database on this cluster, we are are first going to try connecting the default database on it (named `defaultdb`).

1. On your new database's page, you'll see a "Getting Started" dialog -- select it!
2. For "Restrict inbound connections", this is completely optional and beginneers should skip this for now. We skip this because if you'll be running calculations on some supercomputer/cluster, then you'll need to add **ALL** of the associated IP addresses in order for connections to work properly. That's a lot of IP addresses to grab and configure properly -- so we leave this to advanced users.
3. "Connection details" is what we need to give to Simmate/Django. Let's copy this information. As an example, here is what the details look like on DigitalOcean:
```
username = doadmin
password = asd87a9sd867fasd
host = db-postgresql-nyc3-49797-do-user-8843535-0.b.db.ondigitalocean.com
port = 25060
database = defaultdb
sslmode = require
```
5. In your simmate python environment, make sure you have the Postgres engine
installed. The package is `psycopg2`, which let's Django talk with Postgres. To install this, run the command:
``` bash
conda install -n my_env -c conda-forge psycopg2
```

4. We need to pass this information to Simmate (which connects using Django). To do this, add a file named `my_env-database.yaml` (using your conda env name) to your simmate config directory (`~/simmate`) with the following content -- be sure substute in your connection information and note that ENGINE tells Django we are using Postgres:
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
5. Make sure you can connect to this database on your local computer by running the following in Spyder:
``` python
from simmate.configuration.django.settings import DATABASES

print(DATABASES)  # this should give your connect info!
```


### (iv) make a separate the database for testing (on the same server)

Just like how we don't use the `(base)` environment in Anaconda, we don't want to use the default database `defaultdb` on our cluster. Here will make a new database -- one that we can delete if we'd  like to restart.

1. On DigitalOcean with your Database Cluster page, select the "Users&Databases" tab.
2. Create a new database using the "Add new database" button and name this `simmate-database-00`. We name it this way because you may want to make new/separate databases and numbering is a quick way to keep track of these.
3. In your connection settings (from the section above), switch the NAME from defaultdb to `simmate-database-00`. You will change this in your `my_env-database.yaml` file.

### (v) build our database tables

Now that we set up and connected to our database, we can now make our Simmate database tables and start filling them with data! We do this the same way we did without a cloud database:

1. In your terminal, make sure you have you Simmate enviornment activated
2. Run the following command: 
``` bash
simmate database reset
```
3. You're now ready to start using Simmate with your new database!


### (vi) create a connection pool

When we have a bunch of calculations running at once, we need to make sure our database can handle all of these connections. Therefore, we make a connection pool which allows for thousands of connections. This "pool" works like a waitlist where the database handles each connection request in order.

1. Select the "Connection Pools" tab and then "Create a Connection Pool"
2. Name your pool `simmate-database-00-pool` and select `simmate-database-00` for the database
3. Select "Transaction" for our mode (the default) and set our pool size to **10** (or modify this value as you wish)
4. Create the pool when you're ready!
5. You'll have to update your `my_env-database.yaml` file to these connection settings. At this point your file will look similar to this (note, our NAME and PORT values have changed):
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
    Calling `simmate database reset` when using a connection pull will NOT work!
    If you ever need to reset your database, make sure you connect to the database
    directly instead of through a database pool.


### (vii) load third-party data

This step is optional.

With Sqlite, we were able to download a prebuilt database with data from
third-parties already in it. However, creating our postgres database means our
database is entirely empty.

To load **ALL** third-party data (~5GB total), you can use the following command. We can also use Dask to run this in parallel and speed things up. Depending on your internet connection and CPU speed, this can take up to 24hrs.

``` shell
simmate database load-remote-archives --parallel
```

!!! warning
    `--parallel` will use all cores on your CPU. Keep this in mind if you are
    running other programs/calculations on your computer already.

### (viii) sharing the database

If you want to share this database with others, you simply need to have them copy your config file: `my_env-database.yaml`. They won't need to run `simmate database reset` because you did it for them.

-------------------------------------------------------------------------------
