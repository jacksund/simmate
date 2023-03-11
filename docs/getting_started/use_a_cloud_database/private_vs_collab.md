
# Should I set up my own database?

-------------------------------------------------------------------------------

## Share a database with others

A cloud database lets you save your results to a remote computer through an internet connection, and once a database is set up, you can add as many users and connections as you'd like. 

Therefore, if you are part of a team, you only need **ONE** person to setup and manage **ONE** cloud database. Anyone can collaborate if they have a username and password.

-------------------------------------------------------------------------------

## Collaborating with the Warren Lab

We could (theoretically) have the entire scientific community working together and sharing their results. To this end, our Simmate team tries to get as many labs collaborating as possible. If you would like join this effort, simply send an email to **simmate.team@gmail.com** and ask. Once you're on our team, you won't have to setup or manage any cloud database.

!!! note 
    If you decide to collaborate, we will take on the costs of the cloud database for now, but as our database and community grows, we may need help with funding. Until then, don't hesitate to ask for our status.

-------------------------------------------------------------------------------

## Using a private database

If you would instead like a private database for your team, designate one person to be the database manager. Only that person needs to complete the next section (on setting up your cloud database). All other members, wait until you get connection information and then jump to the final section (on connecting to your cloud database).

So to summarize, only create your own cloud database if both of these conditions are met:

1. you prefer a private database instead of Simmate's collaborative effort
2. you are the point-person for managing your team's private database

-------------------------------------------------------------------------------

## Connecting to a cloud database

If you are collaborating with someone that set up a database already, then
connecting to it will be the easiest thing we've done yet! 

Once you have the connection parameters for your cloud database, simply create the file `~/simmate/my_env-database.yaml` and add the connection parameters that your point-person provided. As an example, this `my_env-database.yaml` file gives a `default` database to use:
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

That's it! When you run a new workflow, results will be saved to this cloud database instead of your local file.


!!! danger
    If you lab uses postgres, make sure you have extra database dependencies installed. For postgres, run the command:
    ``` shell
    conda install -n my_env -c conda-forge psycopg2
    ```

!!! tip
    If you would like to share the database with anyone or any other computer, just share this connection file with them.

-------------------------------------------------------------------------------
