
-------------------------------------------------------------------------------

# Connecting to Postgres

Now that you have a Postgres instance running (either in the cloud or via Docker), let's connect Simmate to it.

## 1. Connection Details

Depending on your choice in the previous step, you will have different connection details.

### For DigitalOcean (Option A):
On your database cluster's page, copy the **Connection details**. They will look something like this:
```
username = doadmin
password = your_secure_password
host = db-postgresql-nyc3-12345-do-user-1234567-0.b.db.ondigitalocean.com
port = 25060
database = defaultdb
sslmode = require
```

### For Docker (Option B):
The default connection details for the command used in the previous step are:
```
username = postgres
password = mysecretpassword
host = localhost
port = 5432
database = postgres
```

## 2. Configuring Simmate

The easiest way to configure Simmate is via the command line. Replace the values below with your specific connection details from Step 1:

``` bash
simmate config update "database.engine=django.db.backends.postgresql"
simmate config update "database.host=YOUR_HOST"
simmate config update "database.name=YOUR_DATABASE_NAME"
simmate config update "database.user=YOUR_USERNAME"
simmate config update "database.password=YOUR_PASSWORD"
simmate config update "database.port=YOUR_PORT"
# DigitalOcean also requires sslmode=require (Option A only)
simmate config update "database.options.sslmode=require"
```

Verify the settings are correctly loaded:
``` bash
simmate config show --user-only
```

## 3. Creating a Separate Database (Optional)

!!! note
    If you are using **Docker (Option B)**, you can skip this step. The default `postgres` database is sufficient for local development.

It's best practice for cloud users to create a dedicated database for your Simmate project rather than using `defaultdb`.

1. In the DigitalOcean dashboard, go to the "Settings" tab for your cluster.
2. Scroll down to "Users & Databases" and click "Add New Database".
3. Name it something like `simmate_db_01`.
4. Update your Simmate settings to use this new name:
``` bash
simmate config update "database.name=simmate_db_01"
```

## 4. Initializing the Database

Now that we've connected to our database, we can create the Simmate tables:

1. Run the following command to initialize the database:
``` bash
simmate database reset
```
*(Note: Use `simmate database update` in the future if you add new apps and only want to apply changes without deleting existing data).*

## 5. Creating a Connection Pool (Cloud Only)

!!! note
    If you are using **Docker (Option B)**, you can skip this step. Connection pooling is primarily needed for high-throughput cloud environments.

When running many calculations simultaneously (e.g., on a supercomputer), your database might receive hundreds of simultaneous connection requests. A **connection pool** manages these requests efficiently.

1. In DigitalOcean, go to the "Connection Pools" tab and click "Create a Connection Pool".
2. Name it `simmate-pool`, select your `simmate_db_01` database, and set the mode to "Transaction".
3. Set the pool size (e.g., 20) and click "Create Pool".
4. DigitalOcean will provide NEW connection details for this pool (different port and name). Update your Simmate settings:
``` bash
simmate config update "database.name=simmate-pool"
simmate config update "database.port=25061"  # Pools often use a different port
```

## 6. Loading Third-Party Data

This step is optional but highly recommended if you want to search existing data (like the Materials Project).

To download and load data from a specific provider, use:
``` shell
simmate database download materials-project
```
You can repeat this for other apps like `cod`, `oqmd`, or `jarvis`. Depending on the dataset size and your connection, this can take anywhere from a few minutes to several hours.

## 7. Sharing the Database

To share this database with teammates, you can export your configuration to a file:
``` bash
simmate config write
```
This will create a file (e.g., `settings.yaml` or `{conda_env}-settings.yaml`) in your `~/simmate` directory. Your teammates can place this file in their own Simmate directory to instantly connect to the same shared database.

-------------------------------------------------------------------------------
