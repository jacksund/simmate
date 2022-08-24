
## Connecting to your cloud database

This will be the easiest thing we've done yet! Once you have the connection parameters for your cloud database, simply create the file `~/simmate/my_env-database.yaml` and add the connection parameters that your point-person provided. As an example, this `my_env-database.yaml` file gives a `default` database to use:
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

If you would like to share the database with anyone or any other computer, just share this connection file with them.

