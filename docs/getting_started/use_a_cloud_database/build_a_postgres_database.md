
## Setting up your cloud database

!!! warning
    Make sure you have read the previous section! Setting up a database can be tricky, and the majority of users can avoid it altogether.

Simmate uses Django ORM to build and manage its database, so any Django-supported database can be used with Simmate. This includes PostgreSQL, MariaDB, MySQL, Oracle, SQLite, and others through third-parties. noSQL databases like MongoDB are supported through [djongo](https://github.com/nesdis/djongo). The full documentation for django databases is available [here](https://docs.djangoproject.com/en/4.0/ref/databases/). 

Our team uses SQLite (for local testing) and PostgreSQL (for production), so at the moment, we can only offer guidance on these two backends. You are welcome to use the others, but be wary that we haven't thuroughly tested these backends and won't be able to help you troubleshoot if errors arise.

PostgreSQL is free and open-source, so you can avoid costs and set it up manually. There are many tutorials and guides available on how to do this ([1](https://www.postgresql.org/docs/current/tutorial.html), [2](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database), etc.). However, this is can take a lot of time AND your final database connection may be slower if your team works accross multiple locations. We instead recommend using a database service such as [DigitalOcean](https://www.digitalocean.com/), [Linode](https://www.linode.com/), [GoogleCloud](https://cloud.google.com/), [AWS](aws.amazon.com), [Azure](https://azure.microsoft.com/), or another provider. 

Our team uses DigitialOcean, where the starter database server (~$15/month) is plenty for Simmate usage. You'll only need >10GB if you are running >100,000 structure relaxations or frequently using unitcells with >1000 atoms. We have a separate tutorial on setting up a database with DigitalOcean located [here](https://github.com/jacksund/simmate/tree/main/src/simmate/configuration/digitalocean).

If you decide to use Postgres, you'll also need to install the extra package `psycopg2`, which let's Django talk with Postgres. To install this, run the command:
``` bash
conda install -n my_env -c conda-forge psycopg2
```

