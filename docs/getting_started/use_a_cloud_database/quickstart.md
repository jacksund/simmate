# Using a Cloud Database

-------------------------------------------------------------------------------

## Quick Guide

1. **Consider collaborating!** The public Simmate website is an open collective where all data is sharing publically, even new workflow submissions. By using the public site, our team will handle the management responsibility for the database, and all data contributed becomes public for the community to use.

2. **Establish a cloud database.** Simmate uses **Postgres** as the primary database engine for production system. You have two main options for setting a Postgres database:

    *   **Managed Cloud (Recommended):** The easiest way to set up a Postgres database for beginners is with [DigitalOcean](https://m.do.co/c/8aeef2ea807c). A basic 10GB database (~$15/month) is plenty to get started with, and if you use our referral link, you'll get $200 in free credit for your first 60 days.
        <br>
        [![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%203.svg)](https://www.digitalocean.com/?refcode=8aeef2ea807c&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

    *   **Local Docker (For Practice):** If you want to test Postgres locally for free before moving to the cloud:
        ``` bash
        docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -v ~/simmate/database_volume:/var/lib/postgresql/data -d postgres
        ```

3. **Update your Simmate settings.** You can update your settings directly from the command line (replace with your actual details):
``` shell
simmate config update "database.engine=django.db.backends.postgresql"
simmate config update "database.host=simmate-db.example.com"
simmate config update "database.name=simmate_db"
simmate config update "database.user=doadmin"
simmate config update "database.password=your_password"
simmate config update "database.port=25061"
simmate config update "database.options.sslmode=require"
```
Alternatively, you can manually update the file `~/simmate/settings.yaml` (or `{conda_env}-settings.yaml`) with your connection details that align with the [Django format](https://docs.djangoproject.com/en/5.1/ref/settings/#databases). Your settings file should look like this:
``` yaml
database:
  engine: django.db.backends.postgresql
  host: simmate-db.example.com
  name: simmate-db-pool
  user: doadmin
  password: your_password
  port: 25061
  options:
    sslmode: require
```

4. **Initialize your database.** If you have created a brand new database, you will need to build the initial tables. Use the following command:
``` shell
simmate database reset
```

!!! danger
    **Do NOT execute this command if you have joined a shared database that already has data!**

-------------------------------------------------------------------------------