# Should I Create My Own Database?

-------------------------------------------------------------------------------

## Sharing a Database with Others

A cloud database allows you to store your results on a remote server via an internet connection. Once a database is established, you can add unlimited users and connections. 

If you're part of a team, only **ONE** member needs to set up and manage **ONE** cloud database. Collaboration is possible for anyone with a username and password.

-------------------------------------------------------------------------------

## Collaborating via the Public Website

Ideally, the entire scientific community could work together, sharing their results. Our Simmate team encourages as many labs as possible to collaborate through our public website ([simmate.org](https://simmate.org/)). This operates as an open collective: all data contributed is public, and our team handles all database management responsibilities. This means you won't need to set up or manage any cloud database yourself. For more details on this collaborative effort, please refer to our homepage at [simmate.org](https://simmate.org/).

-------------------------------------------------------------------------------

## Using a Private Database

If you prefer a private database for your team, appoint one member as the database manager. This person alone needs to complete the next section (on setting up your cloud database). All other members should wait for connection information before proceeding to the final section (on connecting to your cloud database).

In summary, only establish your own cloud database if:

1. You prefer a private database over Simmate's collaborative effort.
2. You are the designated manager of your team's private database.

-------------------------------------------------------------------------------

## Connecting to a Cloud Database

If you're collaborating with someone who has already set up a database, connecting to it will be straightforward. 

Once you have your cloud database's connection parameters, update your settings. The easiest way is through the command line (replace with your actual details):
``` shell
simmate config update "database.engine=django.db.backends.postgresql"
simmate config update "database.host=simmate-db.example.com"
simmate config update "database.name=simmate_db"
simmate config update "database.user=doadmin"
simmate config update "database.password=your_password"
simmate config update "database.port=25061"
simmate config update "database.options.sslmode=require"
```

Alternatively, you can manually update the file `~/simmate/settings.yaml` (or `{conda_env}-settings.yaml`) with the following content:
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

-------------------------------------------------------------------------------