# Should I Create My Own Database?

-------------------------------------------------------------------------------

## Sharing a Database with Others

A cloud database allows you to store your results on a remote server via an internet connection. Once a database is established, you can add unlimited users and connections. 

If you're part of a team, only **ONE** member needs to set up and manage **ONE** cloud database. Collaboration is possible for anyone with a username and password.

-------------------------------------------------------------------------------

## Collaborating with the Warren Lab

Ideally, the entire scientific community could work together, sharing their results. Our Simmate team encourages as many labs as possible to collaborate. If you're interested in joining this effort, simply email **simmate.team@gmail.com**. As a team member, you won't need to set up or manage any cloud database.

-------------------------------------------------------------------------------

## Using a Private Database

If you prefer a private database for your team, appoint one member as the database manager. This person alone needs to complete the next section (on setting up your cloud database). All other members should wait for connection information before proceeding to the final section (on connecting to your cloud database).

In summary, only establish your own cloud database if:

1. You prefer a private database over Simmate's collaborative effort.
2. You are the designated manager of your team's private database.

-------------------------------------------------------------------------------

## Connecting to a Cloud Database

If you're collaborating with someone who has already set up a database, connecting to it will be straightforward. 

Once you have your cloud database's connection parameters, create the file `~/simmate/my_env-settings.yaml` (if it isn't there already) and input the connection parameters provided by your point-person. For example, the following can be added to your settings file:
``` yaml
database:
  ENGINE: django.db.backends.postgresql
  HOST: simmate-database-do-user-8843535-0.b.db.ondigitalocean.com
  NAME: simmate-database-00-pool
  USER: doadmin
  PASSWORD: ryGEc5PDxC2IHDSM
  PORT: 25061
  OPTIONS:
    sslmode: require
```

That's all! When you run a new workflow, results will be saved to this cloud database instead of your local file.

!!! danger
    If your lab uses postgres, ensure you have the necessary database dependencies installed. For postgres, execute the command:
    ``` shell
    conda install -n my_env -c conda-forge psycopg2
    ```

-------------------------------------------------------------------------------