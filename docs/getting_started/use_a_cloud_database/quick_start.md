# Use a cloud database

In this tutorial, you will learn how to switch from saving results locally to saving them to a collaborative remote (or "cloud") database.

-------------------------------------------------------------------------------

## The quick tutorial

1. Consider collaborating! Simmate is built for sharing results, so email simmate.team@gmail.com to discuss joining our effort. This will let you avoid the complexities of managing your own database. If you decide to join, you'll only have to complete steps 3 and 4 of this tutorial.

2. Set up a cloud database that is [supported by django](https://docs.djangoproject.com/en/4.0/ref/databases/#third-party-notes). We highly recommend setting up a connection pool for your database as well. If you need help with this setup, you can use our "deploy" button in the next section. 10GB is plenty to get started.

3. Make sure you have extra database dependencies installed. For postgres, run the command:
``` shell
conda install -n my_env -c conda-forge psycopg2
```

4. Add the file `~/simmate/my_env-database.yaml` with your connection details that match [django format](https://docs.djangoproject.com/en/dev/ref/settings/#databases). As an example, this `my_env-database.yaml` file gives a `default` database to use:
``` yaml
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

-------------------------------------------------------------------------------

## Set up using Digital Ocean

We recommend using [Postgres](https://www.postgresql.org/) through [DigitalOcean](https://www.digitalocean.com/). If you do not have a Digital Ocean account, we ask that you sign up using [our referral link](https://m.do.co/c/8aeef2ea807c). The button below will then take you to the relevant page.

Note, we are not affiliated with Digital Ocean -- it's just what our team happens to use.

<!-- button that starts up DigitalOcean app -->
<a href="https://cloud.digitalocean.com/databases/new">
 <img src="https://www.deploytodo.com/do-btn-blue.svg" alt="Deploy to DO">
</a>


-------------------------------------------------------------------------------
