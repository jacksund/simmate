# Utilize a Cloud Database

-------------------------------------------------------------------------------

## Quick Guide

1. Consider joining forces! Simmate is designed for sharing results, so reach out to simmate.team@gmail.com to discuss becoming part of our team. This will help you bypass the complexities of managing your own database. If you decide to join, you'll only need to follow steps 3 and 4 of this guide.

2. Establish a cloud database that is [supported by django](https://docs.djangoproject.com/en/4.0/ref/databases/#third-party-notes). We strongly suggest setting up a connection pool for your database as well. If you need assistance with this setup, you can utilize our "deploy" button in the following section. A 10GB database is sufficient to begin with.

3. Ensure you have the necessary database dependencies installed. For postgres, execute the following command:
``` shell
conda install -n my_env -c conda-forge psycopg2
```

4. Include the file `~/simmate/my_env-database.yaml` with your connection details that align with the [django format](https://docs.djangoproject.com/en/dev/ref/settings/#databases). For instance, this `my_env-database.yaml` file provides a `default` database to use:
``` yaml
default:
  ENGINE: django.db.backends.postgresql
  HOST: simmate-database-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool
  USER: doadmin
  PASSWORD: ryGEc5PDxC2IHDSM
  PORT: 25061
  OPTIONS:
    sslmode: require
```

5. If you have created a brand new database in step 2, you will need to reset your database to build initial tables. Use the command `simmate database reset` to do this. :warning: **Do NOT execute this command if you have joined a shared database!**

-------------------------------------------------------------------------------

## Setup with Digital Ocean

We recommend using [Postgres](https://www.postgresql.org/) via [DigitalOcean](https://www.digitalocean.com/). If you don't have a Digital Ocean account, please sign up using [our referral link](https://m.do.co/c/8aeef2ea807c). The button below will direct you to the appropriate page.

Please note, we are not affiliated with Digital Ocean -- it's simply the platform our team prefers to use.

<!-- button that starts up DigitalOcean app -->
<a href="https://cloud.digitalocean.com/databases/new">
 <img src="https://www.deploytodo.com/do-btn-blue.svg" alt="Deploy to DO">
</a>

-------------------------------------------------------------------------------