# Use a cloud database

In this tutorial, you will learn how to switch from saving results locally to saving them to a collaborative remote (or "cloud") database.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [Should I set up my own database?](#should-i-set-up-my-own-database)
    - [Setting up your cloud database](#setting-up-your-cloud-database)
    - [Connecting to your cloud database](#connecting-to-your-cloud-database)


<br/><br/>

# The quick tutorial

1. Consider collaborating! Simmate is built for sharing results, so email jacksundberg123@gmail.com to discuss joining our effort. This will let you avoid the complexities of managing your own database. If you decide to join, you'll only have to complete step 4 of this tutorial.
2. Set up a cloud database that is [supported by django](https://docs.djangoproject.com/en/4.0/ref/databases/#third-party-notes). We recommend using [Postgres](https://www.postgresql.org/) through [DigitalOcean](https://www.digitalocean.com/).
3. Make sure you have extra database dependencies installed. For postgres, run the command:
```
conda install -n my_env -c conda-forge psycopg2
```
4. Add the file `~/.simmate/database.yaml` with your connection details that match [django format](https://docs.djangoproject.com/en/dev/ref/settings/#databases). As an example, this `database.yaml` file gives a `default` database to use:
```
default:
  ENGINE: django.db.backends.postgresql_psycopg2
  HOST: simmate-database-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool
  USER: doadmin
  PASSWORD: ryGEc5PDxC2IHDSM
  PORT: 25061
  OPTIONS:
    sslmode: require
```
5. And if (and only if) you built a brand new database in step 2, reset your database in order to build initial tables. Use the command `simmate database reset` to do this. :warning: **do NOT run this command if you joined a collaborative database!**

<br/><br/>

# The full tutorial

<br/>

## Should I set up my own database?

A cloud database let's you save your results to a remote computer through an internet connection, and once a database is set up, you can add as many users and connections as you'd like. Therefore, if you are part of a team, you only need ONE person to setup and manage ONE cloud database. Anyone can collaborate if they have a username and password.

So we could (theoretically) have the entire scientific community working together and sharing their results. To this end, our Simmate team tries to get as many labs collaborating as possible. If you would like join this effort, simply send an email to jacksundberg123@gmail.com and ask. Once you're on our team, you won't have to setup or manage any cloud database.

> :bulb: Collaborating with our team is 100% free, and we hope to keep it that way. We take on the costs of the cloud database for now, but as our database and community grows, we may need help with funding. Until then, don't hesitate to ask for our status.

If you would instead like a private database for your team, designate one person to be the database manager. Only that person needs to complete the next section (on setting up your cloud database). All other members, wait until you get connection information and then jump to the final section (on connecting to your cloud database).

So to summarize, only create your own cloud database if both of these conditions are met:
1. you prefer a private database instead of Simmate's collaborative effort
2. you are the point-person for managing your team's private database

<br/>

## Setting up your cloud database

*Make sure you have read the previous section! Setting up a database can be tricky, and the majority of users can avoid it altogether.*

Simmate uses Django ORM to build and manage its database, so any Django-supported database can be used with Simmate. This includes PostgreSQL, MariaDB, MySQL, Oracle, SQLite, and others through third-parties. noSQL databases like MongoDB are supported through [djongo](https://github.com/nesdis/djongo). The full documentation for django databases is available [here](https://docs.djangoproject.com/en/4.0/ref/databases/). Our team uses SQLite (for local testing) and PostgreSQL (for production), so at the moment, we can only offer guidance on these two backends. You are welcome to use the others, but be wary that we haven't thuroughly tested these backends and won't be able to help you troubleshoot if errors arise.

PostgreSQL is free and open-source, so you can avoid costs and set it up manually. There are many tutorials and guides available on how to do this ([1](https://www.postgresql.org/docs/current/tutorial.html), [2](https://www.prisma.io/dataguide/postgresql/setting-up-a-local-postgresql-database), etc.). However, this is can take a lot of time AND your final database connection may be slower if your team works accross multiple locations. We instead recommend using a database service such as [DigitalOcean](https://www.digitalocean.com/), [Linode](https://www.linode.com/), [GoogleCloud](https://cloud.google.com/), [AWS](aws.amazon.com), [Azure](https://azure.microsoft.com/), or another provider. Our team uses DigitialOcean, where the starter database server (~$15/month) is plenty for Simmate usage. You'll only need >10GB if you are running >100,000 structure relaxations or frequently using unitcells with >1000 atoms. We have a separate tutorial on setting up a database with DigitalOcean located [here](https://github.com/jacksund/simmate/tree/main/src/simmate/configuration/digitalocean).

If you decide to use Postgres, you'll also need to install the extra package `psycopg2`, which let's Django talk with Postgres. To install this, run the command `conda install -n my_env -c conda-forge psycopg2`.

Once you have your database set-up, add the connection parameters to `~/.simmate/database.yaml` (see the quick tutorial above for an example) and then run `simmate database reset` to build all of your tables. You can then share your `database.yaml` (or alternatively, make new user profiles and share those connection details) with your team members.

<br/>

## Connecting to your cloud database

This will be the easiest thing we've done yet! Once you have the connection parameters for your cloud database, simply create the file `~/.simmate/database.yaml` and add the connection parameters that your point-person provided. As an example, this `database.yaml` file gives a `default` database to use:
```
default:
  ENGINE: django.db.backends.postgresql_psycopg2
  HOST: simmate-database-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool
  USER: doadmin
  PASSWORD: ryGEc5PDxC2IHDSM
  PORT: 25061
  OPTIONS:
    sslmode: require
```

That's it! When you run a new workflow, results will be saved to this cloud database instead of your local file.

